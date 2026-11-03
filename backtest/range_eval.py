"""Walk-forward evaluation of the range model against the VIX-implied baselines."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from backtest.direction_eval import event_groups
from backtest.walkforward import walk_forward_splits
from features.builder import FeatureSet
from models.range import column_quantiles, range_baselines, range_model_from_config

logger = logging.getLogger(__name__)

SPEC_BASELINE = "baseline_vix_normal"  # the CLAUDE.md VIX-implied range


def pinball_loss(y: np.ndarray, q_pred: np.ndarray, tau: float) -> float:
    """Mean quantile (pinball) loss."""
    d = y - q_pred
    return float(np.mean(np.maximum(tau * d, (tau - 1) * d)))


def interval_metrics(y: pd.Series, pred: pd.DataFrame, bands: list[float]) -> dict[str, float]:
    """Coverage and mean width (in % of price) per band, pinball loss, median abs error."""
    yv = y.to_numpy()
    out: dict[str, float] = {"n": int(len(yv))}
    for b in bands:
        p = int(round(b * 100))
        lo, hi = pred[f"lo{p}"].to_numpy(), pred[f"hi{p}"].to_numpy()
        out[f"coverage_{p}"] = float(np.mean((yv >= lo) & (yv <= hi)))
        out[f"width_{p}_pct"] = float(np.mean(np.exp(hi) - np.exp(lo)) * 100)
    levels = column_quantiles(bands)
    out["pinball"] = float(np.mean([pinball_loss(yv, pred[c].to_numpy(), q) for c, q in levels.items()]))
    out["median_abs_err_pct"] = float(np.median(np.abs(np.exp(yv) - np.exp(pred["med"].to_numpy()))) * 100)
    return out


@dataclass
class RangeReport:
    """Out-of-sample range results for one index and run.

    Attributes:
        predictions: Per name ("model", "baseline_vix_normal", ...) and target, band frames
            (log ratios) with the actual ``y`` attached.
        metrics: name -> target -> metrics.
        splits: name -> target -> subset -> coverage metrics.
        use_model: target -> whether the ML range beats the CLAUDE.md VIX baseline on
            coverage and width for every band (otherwise the baseline is shown).
    """

    predictions: dict[str, dict[str, pd.DataFrame]]
    metrics: dict[str, dict[str, dict[str, float]]]
    splits: dict[str, dict[str, dict[str, dict[str, float]]]]
    use_model: dict[str, bool]
    n_folds: int
    bands: list[float]
    warnings: list[str] = field(default_factory=list)


def range_training_frame(fs: FeatureSet, cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rows with every range target known, after warm-up and ``train_start``."""
    r = cfg["models"]["range"]
    Y = fs.targets[list(r["targets"])]
    keep = Y.notna().all(axis=1).to_numpy().copy()
    keep[: int(r.get("min_history_sessions", 0))] = False
    if r.get("train_start"):
        keep &= np.asarray(fs.features.index >= pd.Timestamp(r["train_start"], tz=fs.features.index.tz))
    return fs.features[keep], Y[keep]


def beats_baseline(model: dict[str, float], base: dict[str, float], bands: list[float], tol: float) -> bool:
    """Coverage error no worse than the baseline's (+ tol) and narrower, for every band."""
    for b in bands:
        p = int(round(b * 100))
        if abs(model[f"coverage_{p}"] - b) > abs(base[f"coverage_{p}"] - b) + tol:
            return False
        if model[f"width_{p}_pct"] >= base[f"width_{p}_pct"]:
            return False
    return True


def evaluate_range(fs: FeatureSet, cfg: dict[str, Any]) -> RangeReport:
    """Walk-forward bands for the range model and baselines, with coverage/width/pinball."""
    r = cfg["models"]["range"]
    bands = sorted(cfg["prediction"]["range_bands"])
    X, Y = range_training_frame(fs, cfg)
    v = cfg["validation"]
    folds = walk_forward_splits(len(X), int(v["min_train_sessions"]),
                                int(r.get("test_sessions", v["test_sessions"])),
                                int(v.get("embargo_sessions", 0)), v.get("max_train_sessions"))
    if not folds:
        raise ValueError(f"not enough rows ({len(X)}) for walk-forward validation")
    makers = {"model": lambda: range_model_from_config(cfg)}
    makers.update({f"baseline_{n}": f for n, f in range_baselines(cfg).items()})

    preds: dict[str, dict[str, list[pd.DataFrame]]] = {n: {t: [] for t in r["targets"]} for n in makers}
    for fold in folds:
        logger.info("range walk-forward fold %d/%d", fold.number + 1, len(folds))
        tr, te = X.iloc[fold.train_idx], X.iloc[fold.test_idx]
        for name, make in makers.items():
            out = make().fit(tr, Y.iloc[fold.train_idx]).predict(te)
            for t, df in out.items():
                preds[name][t].append(df.assign(fold=fold.number))
    joined = {n: {t: pd.concat(v).join(Y[t].rename("y")) for t, v in d.items()} for n, d in preds.items()}

    groups = event_groups(X.loc[joined["model"][r["targets"][0]].index], cfg)
    metrics: dict[str, dict[str, dict[str, float]]] = {}
    splits: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
    for name, per_t in joined.items():
        metrics[name], splits[name] = {}, {}
        for t, df in per_t.items():
            ok = df.drop(columns="fold").notna().all(axis=1)
            metrics[name][t] = interval_metrics(df.loc[ok, "y"], df[ok], bands)
            splits[name][t] = {}
            for g, mask in groups.items():
                m = (mask.reindex(df.index).fillna(False).astype(bool) & ok).to_numpy()
                if m.sum() >= 20:
                    splits[name][t][g] = interval_metrics(df.loc[m, "y"], df[m], bands)

    tol = float(r.get("coverage_tolerance", 0.01))
    use_model = {t: beats_baseline(metrics["model"][t], metrics[SPEC_BASELINE][t], bands, tol)
                 for t in r["targets"]}
    warnings = [f"range {t}: ML bands do not beat the VIX-implied baseline on coverage and width; "
                "the VIX baseline will be shown instead." for t, ok in use_model.items() if not ok]
    for t in r["targets"]:
        for b in bands:
            p = int(round(b * 100))
            cov = metrics["model"][t][f"coverage_{p}"]
            if abs(cov - b) > 0.05:
                warnings.append(f"range {t}: {p}% band covers {cov:.1%} out of sample (far from nominal).")
    for w in warnings:
        logger.warning(w)
    return RangeReport(joined, metrics, splits, use_model, len(folds), bands, warnings)


def range_report_to_dict(rep: RangeReport) -> dict[str, Any]:
    """JSON-serialisable summary."""
    return {"n_folds": rep.n_folds, "bands": rep.bands, "metrics": rep.metrics,
            "splits": rep.splits, "use_model": rep.use_model, "warnings": rep.warnings}


def range_report_markdown(title: str, rep: RangeReport) -> str:
    """Coverage / width / pinball table per target, plus coverage by regime and event."""
    any_df = next(iter(next(iter(rep.predictions.values())).values()))
    lines = [f"## {title}", "", f"Out-of-sample {any_df.index.min().date()} to {any_df.index.max().date()}: "
             f"{len(any_df)} sessions, {rep.n_folds} walk-forward folds. Widths are average band width "
             "in % of price; nominal coverage is the band level.", ""]
    pcts = [int(round(b * 100)) for b in rep.bands]
    head = ["n"] + [f"cov{p}" for p in pcts] + [f"width{p}%" for p in pcts] + ["pinball×1e3", "med abs err%"]
    for t in rep.metrics["model"]:
        lines += [f"### {t.removeprefix('y_')}  (shown: {'ML model' if rep.use_model[t] else 'VIX baseline'})",
                  "", "| source | " + " | ".join(head) + " |", "|---" * (len(head) + 1) + "|"]
        for name in rep.metrics:
            m = rep.metrics[name][t]
            cells = [str(m["n"])] + [f"{m[f'coverage_{p}']:.3f}" for p in pcts] + \
                    [f"{m[f'width_{p}_pct']:.2f}" for p in pcts] + \
                    [f"{m['pinball'] * 1e3:.3f}", f"{m['median_abs_err_pct']:.2f}"]
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
        lines.append("")
        subsets = list(rep.splits["model"][t])
        if subsets:
            lines += ["Coverage by subset (model / VIX baseline):", "",
                      "| subset | n | " + " | ".join(f"cov{p}" for p in pcts) + " |",
                      "|---" * (len(pcts) + 2) + "|"]
            for g in subsets:
                m, b = rep.splits["model"][t][g], rep.splits[SPEC_BASELINE][t].get(g, {})
                cells = [f"{m[f'coverage_{p}']:.3f} / {b.get(f'coverage_{p}', float('nan')):.3f}" for p in pcts]
                lines.append(f"| {g} | {m['n']} | " + " | ".join(cells) + " |")
            lines.append("")
    if rep.warnings:
        lines += ["### Warnings", ""] + [f"- {w}" for w in rep.warnings]
    return "\n".join(lines) + "\n"
