"""Direction model: P(next close > previous close * (1 + threshold)).

Preprocessing (imputation, scaling) lives inside the estimator pipeline, so it is fit
on each training fold only. Calibration is learned on the most recent part of the
training window, never on test data.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

ESTIMATORS = ("logistic", "lightgbm", "xgboost")
_MIN_CALIBRATION_ROWS = 50
_EPS = 1e-6


def make_estimator(name: str, params: dict[str, Any], seed: int) -> Any:
    """Build an unfitted classifier by name."""
    if name == "logistic":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(random_state=seed, **params)),
        ])
    if name == "lightgbm":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(random_state=seed, **params)
    if name == "xgboost":
        from xgboost import XGBClassifier
        return XGBClassifier(random_state=seed, eval_metric="logloss", **params)
    raise ValueError(f"unknown estimator {name!r}; choose from {ESTIMATORS}")


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, _EPS, 1 - _EPS)
    return np.log(p / (1 - p)).reshape(-1, 1)


class DirectionModel:
    """Classifier plus optional probability calibration.

    With calibration, the base model is first fit on the older part of the training
    window and a calibrator is fit on its predictions for the newest part. The base
    model is then refit on the whole window and the calibrator is reused.
    """

    def __init__(self, estimator: str, params: dict[str, Any], calibration: str = "sigmoid",
                 calibration_fraction: float = 0.2, seed: int = 42) -> None:
        if calibration not in ("none", "sigmoid", "isotonic"):
            raise ValueError(f"unknown calibration {calibration!r}")
        self.estimator = estimator
        self.params = params
        self.calibration = calibration
        self.calibration_fraction = calibration_fraction
        self.seed = seed

    def _new(self) -> Any:
        return make_estimator(self.estimator, self.params, self.seed)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "DirectionModel":
        """Fit on time-ordered training rows."""
        self.feature_names_ = list(X.columns)
        y = np.asarray(y, dtype=int)
        self.calibrator_ = None
        n_cal = int(len(X) * self.calibration_fraction)
        if self.calibration != "none" and n_cal >= _MIN_CALIBRATION_ROWS and len(X) - n_cal >= 2 * n_cal:
            base = self._new().fit(X.iloc[:-n_cal], y[:-n_cal])
            raw = base.predict_proba(X.iloc[-n_cal:])[:, 1]
            if self.calibration == "sigmoid":
                self.calibrator_ = LogisticRegression().fit(_logit(raw), y[-n_cal:])
            else:
                self.calibrator_ = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip").fit(
                    raw, y[-n_cal:])
        elif self.calibration != "none":
            logger.info("too few rows (%d) to calibrate; using raw probabilities", len(X))
        self.model_ = self._new().fit(X, y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """``[[P(down), P(up)], ...]`` for each row."""
        X = X.reindex(columns=self.feature_names_)
        raw = self.model_.predict_proba(X)[:, 1]
        if self.calibrator_ is None:
            p = raw
        elif self.calibration == "sigmoid":
            p = self.calibrator_.predict_proba(_logit(raw))[:, 1]
        else:
            p = self.calibrator_.predict(raw)
        p = np.clip(p, _EPS, 1 - _EPS)
        return np.column_stack([1 - p, p])

    def feature_importance(self) -> pd.Series:
        """Importance per feature (gain for trees, |coefficient| for logistic)."""
        m = self.model_
        if self.estimator == "logistic":
            vals = np.abs(m.named_steps["clf"].coef_[0])
        elif self.estimator == "lightgbm":
            vals = m.booster_.feature_importance(importance_type="gain")
        else:
            score = m.get_booster().get_score(importance_type="gain")
            vals = [score.get(f, 0.0) for f in self.feature_names_]
        s = pd.Series(np.asarray(vals, dtype=float), index=self.feature_names_)
        total = s.sum()
        return (s / total if total > 0 else s).sort_values(ascending=False)


def direction_model_from_config(cfg: dict[str, Any], estimator: str | None = None,
                                section: str = "direction") -> DirectionModel:
    """Build a binary :class:`DirectionModel` from ``cfg['models'][section]``.

    Sections without their own ``params`` reuse ``models.direction.params``.
    """
    d = cfg["models"][section]
    name = estimator or d["estimator"]
    params = (d.get("params") or cfg["models"]["direction"]["params"]).get(name, {})
    return DirectionModel(name, dict(params), d.get("calibration", "none"),
                          float(d.get("calibration_fraction", 0.2)), int(cfg["models"]["random_seed"]))
