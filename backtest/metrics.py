"""Classification metrics, calibration, and regime/event splits."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, brier_score_loss, log_loss, precision_score,
                             recall_score, roc_auc_score)

_EPS = 1e-6


def calibration_table(y: pd.Series, p: pd.Series, bins: int = 10) -> pd.DataFrame:
    """Reliability table: mean predicted probability vs observed up-rate per bin."""
    edges = np.linspace(0, 1, bins + 1)
    b = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    df = pd.DataFrame({"bin": b, "p": np.asarray(p), "y": np.asarray(y)})
    t = df.groupby("bin").agg(mean_p=("p", "mean"), frac_up=("y", "mean"), count=("y", "size"))
    t["lo"], t["hi"] = edges[t.index], edges[t.index + 1]
    return t.reset_index()


def expected_calibration_error(y: pd.Series, p: pd.Series, bins: int = 10) -> float:
    """Count-weighted mean |predicted - observed| across calibration bins."""
    t = calibration_table(y, p, bins)
    return float((t["count"] * (t["mean_p"] - t["frac_up"]).abs()).sum() / t["count"].sum())


def classification_metrics(y: pd.Series, p: pd.Series, threshold: float = 0.5,
                           bins: int = 10) -> dict[str, float]:
    """Accuracy, precision, recall, ROC-AUC, Brier, log loss and ECE for P(up) forecasts.

    ROC-AUC is NaN when only one class is present.
    """
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), _EPS, 1 - _EPS)
    if len(y) == 0:
        return {"n": 0}
    pred = (p >= threshold).astype(int)
    two_classes = len(np.unique(y)) == 2
    return {
        "n": int(len(y)),
        "up_rate": float(y.mean()),
        "predicted_up_rate": float(pred.mean()),
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, p)) if two_classes else float("nan"),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "ece": expected_calibration_error(y, p, bins),
    }


def vix_regime(level: pd.Series, low: float, high: float) -> pd.Series:
    """Label each row ``low`` / ``normal`` / ``high`` / ``unknown`` by India VIX level."""
    out = pd.Series("normal", index=level.index, dtype=object)
    out[level < low] = "low"
    out[level > high] = "high"
    out[level.isna()] = "unknown"
    return out


def split_metrics(y: pd.Series, p: pd.Series, groups: dict[str, pd.Series], threshold: float = 0.5,
                  bins: int = 10, min_rows: int = 5) -> dict[str, dict[str, Any]]:
    """Metrics for each named boolean subset (skips subsets smaller than ``min_rows``)."""
    out = {}
    for name, mask in groups.items():
        m = mask.reindex(y.index).fillna(False).astype(bool).to_numpy()
        out[name] = (classification_metrics(y[m], p[m], threshold, bins) if m.sum() >= min_rows
                     else {"n": int(m.sum())})
    return out
