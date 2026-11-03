"""Retrain direction models: walk-forward evaluation vs baselines, then a final fit.

For each index and run (morning/evening):
  1. Build features from the cached data.
  2. Walk-forward evaluate every candidate model and the baselines.
  3. Write reports to ``reports/`` (markdown, JSON, out-of-sample predictions).
  4. Fit the deployed estimator on all rows and save it to ``models/artifacts/``.

Usage:
    python scripts/retrain.py [--index nifty] [--run morning] [--refresh]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest.direction_eval import (evaluate_direction, report_markdown,  # noqa: E402
                                     report_to_dict, training_frame)
from data.calendar import TradingCalendar  # noqa: E402
from data.store import MarketDataStore  # noqa: E402
from features.builder import RUNS, build_dataset  # noqa: E402
from models.artifacts import artifact_path, save_artifact  # noqa: E402
from models.direction import direction_model_from_config  # noqa: E402
from settings import load_config, resolve_path, setup_logging  # noqa: E402

logger = logging.getLogger("retrain")


def retrain_one(store: MarketDataStore, cfg: dict, calendar: TradingCalendar,
                index_name: str, run: str, reports_dir: Path) -> dict:
    """Evaluate and retrain the direction model for one index/run. Returns the summary."""
    fs = build_dataset(store, cfg, calendar, index_name, run)
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


def main(argv: list[str] | None = None) -> int:
    """Run retraining. Returns 1 if any index/run failed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--index", choices=None, help="only this index (e.g. nifty)")
    parser.add_argument("--run", choices=RUNS, help="only this run")
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
            try:
                retrain_one(store, cfg, calendar, index_name, run, reports_dir)
            except Exception:
                logger.exception("retrain failed for %s/%s", index_name, run)
                failures += 1
    logger.info("reports written to %s", reports_dir)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
