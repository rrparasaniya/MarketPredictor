"""Walk-forward evaluation of direction models against baselines."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from backtest.metrics import calibration_table, classification_metrics, split_metrics, vix_regime
from backtest.walkforward import splits_from_config, walk_forward_predict
from features.builder import FeatureSet
from models.baselines import all_baselines
from models.direction import direction_model_from_config

logger = logging.getLogger(__name__)


@dataclass
class DirectionReport:
    """Out-of-sample results for one index and run.

    Attributes:
        predictions: Per test session: ``y``, ``fold``, and ``p_<name>`` per model/baseline.
        metrics: Overall metrics per model/baseline.
        splits: Metrics per model/baseline for VIX regimes and event days.
        calibration: Reliability table per model/baseline.
        best_baseline: Baseline with the lowest log loss.
        beats_baseline: Per model: log loss clearly lower than the best baseline
            (positive mean gain with paired t-stat >= ``min_improvement_t_stat``).
        warnings: Problems that need investigating (e.g. suspiciously high accuracy).
    """

    predictions: pd.DataFrame
    metrics: dict[str, dict[str, float]]
    splits: dict[str, dict[str, dict[str, Any]]]
    calibration: dict[str, pd.DataFrame]
    best_baseline: str | None
    beats_baseline: dict[str, bool]
    n_folds: int
    warnings: list[str] = field(default_factory=list)


def log_loss_improvement(y: pd.Series, p_model: pd.Series, p_base: pd.Series) -> tuple[float, float]:
    """Mean per-session log-loss reduction of the model vs a baseline, and its t-statistic.

    Positive means the model is better. A paired test on the same sessions, so a tiny
    gain from luck doesn't count as beating the baseline.
    """
    yv = np.asarray(y, dtype=float)

    def per_row(p: pd.Series) -> np.ndarray:
        q = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
        return -(yv * np.log(q) + (1 - yv) * np.log(1 - q))

    d = per_row(p_base) - per_row(p_model)
    se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else np.nan
    t = float(d.mean() / se) if se and se > 0 else 0.0
    return float(d.mean()), t


def training_frame(fs: FeatureSet, cfg: dict[str, Any], y: pd.Series | None = None,
                   section: str = "direction") -> tuple[pd.DataFrame, pd.Series]:
    """Rows usable for training a binary model.

    Drops rows with an unknown label, the first ``min_history_sessions`` rows, and rows
    before ``train_start`` (if set) from ``cfg['models'][section]``.

    Args:
        fs: Feature set.
        cfg: Project config.
        y: Binary label (NaN = unknown). Defaults to ``y_direction``.
        section: Model config section.
    """
    mcfg = cfg["models"][section]
    y = fs.targets["y_direction"] if y is None else y
    keep = y.notna().to_numpy().copy()
    keep[: int(mcfg.get("min_history_sessions", 0))] = False
    if mcfg.get("train_start"):
        keep &= np.asarray(fs.features.index >= pd.Timestamp(mcfg["train_start"], tz=fs.features.index.tz))
    return fs.features[keep], y[keep].astype(int)


def event_groups(test_X: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, pd.Series]:
    """Boolean masks for VIX regimes and event days (for split metrics)."""
    rep_cfg = cfg["reporting"]
    groups: dict[str, pd.Series] = {}
    if "indiavix_level" in test_X:
        regime = vix_regime(test_X["indiavix_level"], **rep_cfg["vix_regimes"])
        for r in ("low", "normal", "high"):
            groups[f"vix_{r}"] = regime == r
    for col in rep_cfg.get("event_columns", []):
        if col in test_X:
            groups[col] = test_X[col] == 1
            groups[f"not_{col}"] = test_X[col] == 0
    return groups


def evaluate_direction(fs: FeatureSet, cfg: dict[str, Any],
                       candidates: list[str] | None = None) -> DirectionReport:
    """Walk-forward evaluation of the direction models vs the direction baselines."""
    return evaluate_binary(
        fs, cfg, fs.targets["y_direction"], "direction",
        all_baselines(float(cfg["prediction"]["direction_threshold"])),
        sanity_limit=float(cfg["reporting"]["accuracy_sanity_limit"]), candidates=candidates)


def evaluate_binary(fs: FeatureSet, cfg: dict[str, Any], label: pd.Series, section: str,
                    baselines: dict[str, Any], sanity_limit: float | None = None,
                    candidates: list[str] | None = None) -> DirectionReport:
    """Walk-forward predictions and metrics for each candidate model and baseline.

    Args:
        fs: Feature set.
        cfg: Project config.
        label: Binary target per session (NaN = unknown).
        section: Model config section (``direction`` or ``gap``).
        baselines: Name -> factory for baseline classifiers.
        sanity_limit: Flag model accuracy above this as a probable leak (None = no check).
        candidates: Estimators to evaluate (defaults to the section's candidates).
    """
    X, y = training_frame(fs, cfg, label, section)
    folds = splits_from_config(len(X), cfg)
    if not folds:
        raise ValueError(f"not enough rows ({len(X)}) for walk-forward validation")
    rep_cfg = cfg["reporting"]
    mcfg = cfg["models"][section]
    thr = float(mcfg.get("decision_threshold", 0.5))
    bins = int(rep_cfg.get("calibration_bins", 10))
    candidates = candidates or list(mcfg["candidates"])

    makers: dict[str, Any] = {f"model_{c}": (lambda c=c: direction_model_from_config(cfg, c, section))
                              for c in candidates}
    makers.update({f"baseline_{n}": f for n, f in baselines.items()})

    preds = None
    for name, make in makers.items():
        logger.info("walk-forward %s: %s over %d folds", section, name, len(folds))
        p = walk_forward_predict(X, y, make, folds)
        if preds is None:
            preds = pd.DataFrame({"y": y.loc[p.index], "fold": p["fold"]})
        preds[f"p_{name}"] = p["p"]
    assert preds is not None

    yt = preds["y"]
    groups = event_groups(X.loc[preds.index], cfg)

    metrics, splits, calib = {}, {}, {}
    for name in makers:
        p = preds[f"p_{name}"]
        metrics[name] = classification_metrics(yt, p, thr, bins)
        splits[name] = split_metrics(yt, p, groups, thr, bins)
        calib[name] = calibration_table(yt, p, bins)

    base_names = [n for n in makers if n.startswith("baseline_")]
    best_baseline = min(base_names, key=lambda n: metrics[n]["log_loss"])
    min_t = float(rep_cfg.get("min_improvement_t_stat", 2.0))
    beats = {}
    for n in makers:
        if n.startswith("model_"):
            diff, t = log_loss_improvement(yt, preds[f"p_{n}"], preds[f"p_{best_baseline}"])
            metrics[n]["log_loss_gain_vs_best_baseline"] = diff
            metrics[n]["log_loss_gain_t_stat"] = t
            beats[n] = bool(diff > 0 and t >= min_t)

    warnings = []
    for name in makers:
        acc = metrics[name]["accuracy"]
        if sanity_limit is not None and name.startswith("model_") and acc > sanity_limit:
            limit = sanity_limit
            warnings.append(f"{name}: accuracy {acc:.3f} > {limit:.2f}. Treat as a probable "
                            "leak or bug and investigate before using these results.")
    for name, ok in beats.items():
        if not ok:
            m = metrics[name]
            warnings.append(f"{name}: does not clearly beat the best baseline ({best_baseline}): "
                            f"log-loss gain {m['log_loss_gain_vs_best_baseline']:+.4f}, "
                            f"t={m['log_loss_gain_t_stat']:.2f} (needs > 0 and t >= {min_t:.1f}).")
    for w in warnings:
        logger.warning(w)
    return DirectionReport(preds, metrics, splits, calib, best_baseline, beats, len(folds), warnings)


def report_to_dict(rep: DirectionReport) -> dict[str, Any]:
    """JSON-serialisable summary of a report."""
    def clean(o: Any) -> Any:
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, float) and np.isnan(o):
            return None
        return o
    p = rep.predictions
    return clean({
        "test_start": p.index.min().date().isoformat() if len(p) else None,
        "test_end": p.index.max().date().isoformat() if len(p) else None,
        "n_test": int(len(p)), "n_folds": rep.n_folds,
        "metrics": rep.metrics, "splits": rep.splits,
        "best_baseline": rep.best_baseline, "beats_baseline": rep.beats_baseline,
        "warnings": rep.warnings,
        "calibration": {k: v.to_dict(orient="records") for k, v in rep.calibration.items()},
    })


def report_markdown(title: str, rep: DirectionReport) -> str:
    """Human-readable report: overall metrics, splits, and warnings."""
    cols = ["n", "accuracy", "precision", "recall", "roc_auc", "brier", "log_loss", "ece"]
    lines = [f"## {title}", ""]
    p = rep.predictions
    lines.append(f"Out-of-sample {p.index.min().date()} to {p.index.max().date()}: "
                 f"{len(p)} sessions, {rep.n_folds} walk-forward folds. "
                 f"Up-rate {p['y'].mean():.3f}.")
    lines += ["", "| model | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for name, m in rep.metrics.items():
        cells = [f"{m[c]:.3f}" if isinstance(m.get(c), float) else str(m.get(c, "")) for c in cols]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += ["", f"Best baseline (log loss): `{rep.best_baseline}`. Clearly beats it "
              "(paired log-loss gain, t-stat): "
              + ", ".join(f"`{k}`={'yes' if v else 'no'} ({rep.metrics[k]['log_loss_gain_vs_best_baseline']:+.4f}, "
                          f"t={rep.metrics[k]['log_loss_gain_t_stat']:.2f})"
                          for k, v in rep.beats_baseline.items()), ""]
    lines += ["### Accuracy / ROC-AUC by regime and event", "",
              "| subset | n | " + " | ".join(rep.metrics) + " |", "|---" * (len(rep.metrics) + 2) + "|"]
    any_model = next(iter(rep.splits.values()))
    for subset in any_model:
        n = any_model[subset].get("n", 0)
        cells = []
        for name in rep.metrics:
            m = rep.splits[name][subset]
            cells.append("—" if "accuracy" not in m else
                         f"{m['accuracy']:.3f} / " + ("—" if m["roc_auc"] != m["roc_auc"] else f"{m['roc_auc']:.3f}"))
        lines.append(f"| {subset} | {n} | " + " | ".join(cells) + " |")
    if rep.warnings:
        lines += ["", "### Warnings", ""] + [f"- {w}" for w in rep.warnings]
    return "\n".join(lines) + "\n"
