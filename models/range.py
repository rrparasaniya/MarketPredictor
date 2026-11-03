"""Range model: quantile bands for the next session's open, high and low.

Targets are log ratios to the previous close (``y_open``, ``y_high``, ``y_low``). The
model works on VIX-scaled moves (target / implied 1-day sigma), which keeps the problem
comparable across calm and volatile years, then scales back.

Bands use conformalized quantile regression (CQR): quantile models are fit on the older
part of the training window, and each band is widened or narrowed by the amount needed
to reach its nominal coverage on the newest part. No test data is involved.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

logger = logging.getLogger(__name__)

_MIN_CALIBRATION_ROWS = 50


def band_columns(bands: list[float]) -> list[str]:
    """Output columns ordered low to high, e.g. ``[lo95, lo68, med, hi68, hi95]``."""
    pct = sorted((int(round(b * 100)) for b in bands), reverse=True)
    return [f"lo{p}" for p in pct] + ["med"] + [f"hi{p}" for p in reversed(pct)]


def column_quantiles(bands: list[float]) -> dict[str, float]:
    """Quantile level for each output column (``lo95`` -> 0.025, ``med`` -> 0.5, ...)."""
    out = {"med": 0.5}
    for b in bands:
        p = int(round(b * 100))
        out[f"lo{p}"], out[f"hi{p}"] = (1 - b) / 2, 1 - (1 - b) / 2
    return out


def _scale(X: pd.DataFrame, col: str, fallback: str | None) -> pd.Series:
    s = X[col] if col in X else pd.Series(np.nan, index=X.index)
    if fallback and fallback in X:
        s = s.fillna(X[fallback])
    return s.where(s > 0)


def make_consistent(preds: dict[str, pd.DataFrame], cols: list[str]) -> dict[str, pd.DataFrame]:
    """Sort quantiles within each row, and keep high >= open >= low at every level."""
    out = {}
    for t, df in preds.items():
        v = np.sort(df[cols].to_numpy(), axis=1)
        out[t] = pd.DataFrame(v, index=df.index, columns=cols)
    if {"y_open", "y_high"} <= set(out):
        out["y_high"] = np.maximum(out["y_high"], out["y_open"])
    if {"y_open", "y_low"} <= set(out):
        out["y_low"] = np.minimum(out["y_low"], out["y_open"])
    return out


class RangeModel:
    """Conformalized LightGBM quantile regression for open/high/low."""

    def __init__(self, targets: list[str], bands: list[float], params: dict[str, Any],
                 scale_column: str, fallback_scale_column: str | None = None,
                 calibration_fraction: float = 0.2, seed: int = 42) -> None:
        self.targets = targets
        self.bands = sorted(bands)
        self.params = params
        self.scale_column = scale_column
        self.fallback_scale_column = fallback_scale_column
        self.calibration_fraction = calibration_fraction
        self.seed = seed
        self.columns = band_columns(self.bands)
        self.levels = column_quantiles(self.bands)

    def _fit_quantile(self, X: pd.DataFrame, z: pd.Series, q: float) -> Any:
        from lightgbm import LGBMRegressor
        return LGBMRegressor(objective="quantile", alpha=q, random_state=self.seed,
                             **self.params).fit(X, z)

    def fit(self, X: pd.DataFrame, Y: pd.DataFrame) -> "RangeModel":
        """Fit on time-ordered rows. ``Y`` has one column per target (log ratios)."""
        self.feature_names_ = list(X.columns)
        s = _scale(X, self.scale_column, self.fallback_scale_column)
        self.models_: dict[str, dict[float, Any]] = {}
        self.corrections_: dict[str, dict[float, float]] = {}
        for t in self.targets:
            ok = (s.notna() & Y[t].notna()).to_numpy()
            Xt, zt = X[ok], (Y[t] / s)[ok]
            n_cal = int(len(Xt) * self.calibration_fraction)
            do_cal = n_cal >= _MIN_CALIBRATION_ROWS
            fit_X, fit_z = (Xt.iloc[:-n_cal], zt.iloc[:-n_cal]) if do_cal else (Xt, zt)
            self.models_[t] = {q: self._fit_quantile(fit_X, fit_z, q) for q in sorted(set(self.levels.values()))}
            self.corrections_[t] = {}
            if not do_cal:
                logger.info("%s: too few rows to conformalize; using raw quantiles", t)
                continue
            cal_X, cal_z = Xt.iloc[-n_cal:], zt.iloc[-n_cal:].to_numpy()
            for b in self.bands:
                lo = self.models_[t][(1 - b) / 2].predict(cal_X)
                hi = self.models_[t][1 - (1 - b) / 2].predict(cal_X)
                scores = np.maximum(lo - cal_z, cal_z - hi)
                level = min(1.0, np.ceil((n_cal + 1) * b) / n_cal)
                self.corrections_[t][b] = float(np.quantile(scores, level))
        return self

    def predict(self, X: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Per target, a frame of band columns in log-ratio-to-previous-close units."""
        X = X.reindex(columns=self.feature_names_)
        s = _scale(X, self.scale_column, self.fallback_scale_column).to_numpy()
        out = {}
        for t in self.targets:
            df = pd.DataFrame(index=X.index)
            for col, q in self.levels.items():
                df[col] = self.models_[t][q].predict(X)
            for b, c in self.corrections_[t].items():
                p = int(round(b * 100))
                df[f"lo{p}"] -= c
                df[f"hi{p}"] += c
            out[t] = df[self.columns].mul(s, axis=0)
        return make_consistent(out, self.columns)


class VixNormalRange:
    """CLAUDE.md baseline: normal bands of +/- z * VIX-implied 1-day sigma around the previous close."""

    name = "vix_normal"

    def __init__(self, targets: list[str], bands: list[float], scale_column: str) -> None:
        self.targets, self.bands, self.scale_column = targets, sorted(bands), scale_column
        self.columns = band_columns(self.bands)
        self.levels = column_quantiles(self.bands)

    def fit(self, X: pd.DataFrame, Y: pd.DataFrame) -> "VixNormalRange":
        return self

    def predict(self, X: pd.DataFrame) -> dict[str, pd.DataFrame]:
        s = _scale(X, self.scale_column, None)
        df = pd.DataFrame({c: norm.ppf(q) * s for c, q in self.levels.items()}, index=X.index)
        return {t: df[self.columns].copy() for t in self.targets}


class VixEmpiricalRange(VixNormalRange):
    """Stronger baseline: training-window quantiles of (target / VIX sigma), times today's sigma."""

    name = "vix_empirical"

    def fit(self, X: pd.DataFrame, Y: pd.DataFrame) -> "VixEmpiricalRange":
        s = _scale(X, self.scale_column, None)
        self.z_quantiles_ = {}
        for t in self.targets:
            z = (Y[t] / s).dropna()
            self.z_quantiles_[t] = {c: float(np.quantile(z, q)) for c, q in self.levels.items()}
        return self

    def predict(self, X: pd.DataFrame) -> dict[str, pd.DataFrame]:
        s = _scale(X, self.scale_column, None)
        out = {t: pd.DataFrame({c: self.z_quantiles_[t][c] * s for c in self.columns}, index=X.index)
               for t in self.targets}
        return make_consistent(out, self.columns)


def range_model_from_config(cfg: dict[str, Any]) -> RangeModel:
    """Build a :class:`RangeModel` from ``cfg['models']['range']``."""
    r = cfg["models"]["range"]
    return RangeModel(list(r["targets"]), list(cfg["prediction"]["range_bands"]), dict(r["params"]),
                      r["scale_column"], r.get("fallback_scale_column"),
                      float(r.get("calibration_fraction", 0.2)), int(cfg["models"]["random_seed"]))


def range_baselines(cfg: dict[str, Any]) -> dict[str, Any]:
    """Factories for the range baselines."""
    r = cfg["models"]["range"]
    args = (list(r["targets"]), list(cfg["prediction"]["range_bands"]), r["scale_column"])
    return {VixNormalRange.name: lambda: VixNormalRange(*args),
            VixEmpiricalRange.name: lambda: VixEmpiricalRange(*args)}
