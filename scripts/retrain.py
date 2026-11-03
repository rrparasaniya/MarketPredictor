"""Retrain all models: walk-forward evaluation vs baselines, then a final fit.

For each index and run (morning/evening), and each model kind (direction, gap, range):
  1. Build features from the cached data.
  2. Walk-forward evaluate the model(s) and the baselines.
  3. Write reports to ``reports/`` (markdown, JSON, out-of-sample predictions).
  4. Fit the deployed model on all rows and save it to ``models/artifacts/``.

Usage:
    python scripts/retrain.py [--index nifty] [--run morning] [--kind range] [--refresh]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd  # noqa: F401  (used in type hints)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest.direction_eval import (evaluate_binary, evaluate_direction,  # noqa: E402
                                     report_markdown, report_to_dict, training_frame)
from backtest.range_eval import (evaluate_range, range_report_markdown,  # noqa: E402
                                 range_report_to_dict, range_training_frame)
from features.targets import GAP_DOWN, GAP_UP  # noqa: E402
from models.baselines import gap_baselines  # noqa: E402
from models.range import range_model_from_config  # noqa: E402
from data.calendar import TradingCalendar  # noqa: E402
from data.store import MarketDataStore  # noqa: E402
from features.builder import RUNS, build_dataset  # noqa: E402
from models.artifacts import artifact_path, save_artifact  # noqa: E402
from models.direction import direction_model_from_config  # noqa: E402
from settings import load_config, resolve_path, setup_logging  # noqa: E402

logger = logging.getLogger("retrain")

KINDS = ("direction", "gap", "range")


def retrain_direction(fs, cfg: dict, index_name: str, run: str, reports_dir: Path) -> dict:
    """Evaluate and retrain the direction model for one index/run. Returns the summary."""
    rep = evaluate_direction(fs, cfg)
    tag = f"direction_{index_name}_{run}"
    summary = report_to_dict(rep)
    (reports_dir / f"{tag}.json").write_text(json.dumps(summary, indent=2))
    rep.predictions.to_csv(reports_dir / f"{tag}_oos.csv")
    md = report_markdown(f"Direction: {index_name} ({run} run)", rep)

    X, y = training_frame(fs, cfg)
    estimator = cfg["models"]["direction"]["estimator"]
    model = direction_model_from_config(cfg, estimator).fit(X, y)
    top = model.feature_importance().head(15)
    md += "\n### Top features (final model)\n\n" + "\n".join(
        f"- `{k}`: {v:.3f}" for k, v in top.items()) + "\n"
    (reports_dir / f"{tag}.md").write_text(md)

    meta = {
        "kind": "direction", "index": index_name, "run": run, "estimator": estimator,
        "features": list(X.columns), "n_train": int(len(X)),
        "trained_through": X.index.max().date().isoformat(),
        "last_cutoff": fs.meta.loc[X.index.max(), "cutoff"].isoformat(),
        "oos_metrics": summary["metrics"].get(f"model_{estimator}"),
        "best_baseline": rep.best_baseline,
        "beats_baseline": rep.beats_baseline.get(f"model_{estimator}", False),
        "warnings": rep.warnings,
    }
    save_artifact(artifact_path(cfg, "direction", index_name, run), model, meta)
    logger.info("%s: saved model trained through %s (beats baseline: %s)",
                tag, meta["trained_through"], meta["beats_baseline"])
    return summary


def gap_labels(fs) -> dict[str, "pd.Series"]:
    """Binary labels for gap up and gap down (NaN where the open is unknown)."""
    g = fs.targets["y_gap"]
    return {"up": (g == GAP_UP).astype(float).where(g.notna()),
            "down": (g == GAP_DOWN).astype(float).where(g.notna())}


def retrain_gap(fs, cfg: dict, index_name: str, run: str, reports_dir: Path) -> dict:
    """Evaluate and retrain the gap-up and gap-down models for one index/run."""
    thr = float(cfg["prediction"]["gap_threshold"])
    estimator = cfg["models"]["gap"]["estimator"]
    tag = f"gap_{index_name}_{run}"
    md, summary, models, meta_side = "", {}, {}, {}
    for side, label in gap_labels(fs).items():
        rep = evaluate_binary(fs, cfg, label, "gap", gap_baselines(side, thr))
        summary[side] = report_to_dict(rep)
        rep.predictions.to_csv(reports_dir / f"{tag}_{side}_oos.csv")
        md += report_markdown(f"Gap {side}: {index_name} ({run} run)", rep) + "\n"
        X, y = training_frame(fs, cfg, label, "gap")
        models[side] = direction_model_from_config(cfg, estimator, "gap").fit(X, y)
        meta_side[side] = {"beats_baseline": rep.beats_baseline.get(f"model_{estimator}", False),
                           "best_baseline": rep.best_baseline,
                           "oos_metrics": summary[side]["metrics"].get(f"model_{estimator}")}
    (reports_dir / f"{tag}.json").write_text(json.dumps(summary, indent=2))
    (reports_dir / f"{tag}.md").write_text(md)
    meta = {"kind": "gap", "index": index_name, "run": run, "estimator": estimator,
            "features": list(X.columns), "trained_through": X.index.max().date().isoformat(),
            "gap_threshold": thr, **{f"{k}_{side}": v for side, d in meta_side.items() for k, v in d.items()}}
    save_artifact(artifact_path(cfg, "gap", index_name, run), models, meta)
    logger.info("%s: saved (beats baseline: up=%s down=%s)", tag,
                meta["beats_baseline_up"], meta["beats_baseline_down"])
    return summary


def retrain_range(fs, cfg: dict, index_name: str, run: str, reports_dir: Path) -> dict:
    """Evaluate and retrain the range model for one index/run."""
    rep = evaluate_range(fs, cfg)
    tag = f"range_{index_name}_{run}"
    summary = range_report_to_dict(rep)
    (reports_dir / f"{tag}.json").write_text(json.dumps(summary, indent=2))
    (reports_dir / f"{tag}.md").write_text(range_report_markdown(f"Range: {index_name} ({run} run)", rep))
    X, Y = range_training_frame(fs, cfg)
    model = range_model_from_config(cfg).fit(X, Y)
    meta = {"kind": "range", "index": index_name, "run": run, "features": list(X.columns),
            "trained_through": X.index.max().date().isoformat(), "use_model": rep.use_model,
            "bands": rep.bands, "scale_column": cfg["models"]["range"]["scale_column"],
            "oos_metrics": rep.metrics["model"], "warnings": rep.warnings}
    save_artifact(artifact_path(cfg, "range", index_name, run), model, meta)
    logger.info("%s: saved (ML range used: %s)", tag, rep.use_model)
    return summary


RETRAINERS = {"direction": retrain_direction, "gap": retrain_gap, "range": retrain_range}


def main(argv: list[str] | None = None) -> int:
    """Run retraining. Returns 1 if anything failed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--index", help="only this index (e.g. nifty)")
    parser.add_argument("--run", choices=RUNS, help="only this run")
    parser.add_argument("--kind", choices=KINDS, help="only this model kind")
    parser.add_argument("--refresh", action="store_true", help="update data before training")
    parser.add_argument("--config", help="path to config.yaml")
    args = parser.parse_args(argv)

    setup_logging()
    cfg = load_config(args.config)
    calendar = TradingCalendar.from_config(cfg)
    store = MarketDataStore(cfg)
    if args.refresh:
        store.update_all()
    reports_dir = resolve_path(cfg["reporting"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for index_name in [args.index] if args.index else list(cfg["indices"]):
        for run in [args.run] if args.run else RUNS:
            fs = build_dataset(store, cfg, calendar, index_name, run)
            for kind in [args.kind] if args.kind else KINDS:
                try:
                    RETRAINERS[kind](fs, cfg, index_name, run, reports_dir)
                except Exception:
                    logger.exception("retrain failed for %s %s/%s", kind, index_name, run)
                    failures += 1
    logger.info("reports written to %s", reports_dir)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
