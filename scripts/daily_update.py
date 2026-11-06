"""Daily update: fetch data, work out the target session, predict direction, gap and range.

Predictions are appended to ``<processed_dir>/predictions.csv`` with the data cutoff
and the previous session they were based on.

Usage:
    python scripts/daily_update.py [--full] [--now 2026-11-03T08:45+05:30]
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.calendar import TradingCalendar  # noqa: E402
from data.optional_inputs import load_all_optional_inputs  # noqa: E402
from data.store import MarketDataStore  # noqa: E402
from data.timing import (inputs_are_current, resolve_prediction_target,  # noqa: E402
                         run_for_target)
from features.builder import build_dataset  # noqa: E402
from models.artifacts import artifact_path, load_artifact  # noqa: E402
from settings import ist, load_config, resolve_path, setup_logging  # noqa: E402

logger = logging.getLogger("daily_update")


def main(argv: list[str] | None = None) -> int:
    """Run the update. Returns a process exit code (1 if an index failed)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--full", action="store_true", help="re-download full history")
    parser.add_argument("--now", help="override current time (ISO, tz-aware) for testing")
    parser.add_argument("--config", help="path to config.yaml")
    args = parser.parse_args(argv)

    setup_logging()
    cfg = load_config(args.config)
    now = datetime.fromisoformat(args.now) if args.now else datetime.now(ist(cfg))
    calendar = TradingCalendar.from_config(cfg)
    target = resolve_prediction_target(now, calendar, cfg)
    logger.info("now=%s mode=%s target=%s (%s) generate_new=%s",
                target.as_of.isoformat(), target.mode.value, target.target_date,
                target.label, target.generate_new)

    store = MarketDataStore(cfg, now_fn=lambda: now)
    results = store.update_all(full=args.full)
    for r in results:
        logger.info("%-10s ok=%-5s rows=%-5d last_session=%s available_at=%s %s",
                    r.ticker, r.ok, r.rows, r.last_session,
                    r.last_available_at.isoformat() if r.last_available_at is not None else None,
                    r.message)
    optional = load_all_optional_inputs(cfg)
    logger.info("optional inputs loaded: %s", sorted(optional) or "none")

    index_tickers = {idx["ticker"] for idx in cfg["indices"].values()}
    failed = [r.ticker for r in results if r.ticker in index_tickers and r.rows == 0]
    if failed:
        logger.error("no data for required indices: %s", failed)
        return 1

    if not target.generate_new:
        logger.info("market is open: showing the existing prediction, not building a new one")
        return 0
    run = run_for_target(target, cfg)
    logger.info("using the %s models", run)
    tdates = pd.DatetimeIndex([pd.Timestamp(target.target_date)]).tz_localize(cfg["timezone"])
    for name in cfg["indices"]:
        fs = build_dataset(store, cfg, calendar, name, run, target_dates=tdates,
                           cutoffs=pd.Series([pd.Timestamp(target.as_of)], index=tdates))
        row, meta = fs.features.iloc[0], fs.meta.iloc[0]
        missing = sorted(row.index[row.isna()])
        logger.info("%s %s run: target=%s cutoff=%s prev_session=%s prev_close=%.2f "
                    "features=%d missing=%d %s", name, run, target.target_date,
                    meta["cutoff"].isoformat(), meta["prev_session"].date(), meta["prev_close"],
                    len(row), len(missing), missing[:8])
        if not inputs_are_current(meta["prev_session"].date(), target.target_date, calendar):
            logger.warning("%s: latest final bar is %s, not the session before %s; skipping this "
                           "forecast (the day's bar may not be final yet, or data is missing)",
                           name, meta["prev_session"].date(), target.target_date)
            continue
        for col in [c for c in meta.index if c.endswith("_available_at") and pd.notna(meta[c])]:
            logger.info("  data used: %-28s session=%s available_at=%s", col.removesuffix("_available_at"),
                        meta[col.replace("available_at", "session")].date()
                        if col != "idx_available_at" else meta["prev_session"].date(),
                        meta[col].isoformat())
        record = predict_direction(cfg, name, run, fs, target)
        if record is not None:
            record.update(predict_gap(cfg, name, run, fs))
            record.update(predict_range(cfg, name, run, fs))
            record["data_refresh_ok"] = all(r.ok for r in results)
            append_prediction(cfg, record)
    return 0


def predict_gap(cfg: dict, index_name: str, run: str, fs) -> dict:
    """P(gap up / flat / down) for the live row, or {} if no gap model is trained."""
    loaded = load_artifact(artifact_path(cfg, "gap", index_name, run))
    if loaded is None:
        logger.warning("%s/%s: no trained gap model", index_name, run)
        return {}
    models, meta = loaded
    up = float(models["up"].predict_proba(fs.features)[0, 1])
    down = float(models["down"].predict_proba(fs.features)[0, 1])
    total = up + down
    if total > 1:  # two separate models can overshoot; renormalise
        up, down = up / total, down / total
    flat = max(0.0, 1 - up - down)
    logger.info("%s %s gap (threshold %.2f%%): up %.2f | flat %.2f | down %.2f", index_name, run,
                meta["gap_threshold"] * 100, up, flat, down)
    return {"p_gap_up": round(up, 4), "p_gap_flat": round(flat, 4), "p_gap_down": round(down, 4),
            "gap_model_beats_baseline": bool(meta["beats_baseline_up"] and meta["beats_baseline_down"])}


def predict_range(cfg: dict, index_name: str, run: str, fs) -> dict:
    """Open/high/low bands in index points for the live row, or {} if no range model.

    For each target, uses the ML bands only if they beat the VIX-implied baseline out of
    sample; otherwise shows the VIX baseline (CLAUDE.md rule 3).
    """
    from models.range import VixNormalRange

    loaded = load_artifact(artifact_path(cfg, "range", index_name, run))
    if loaded is None:
        logger.warning("%s/%s: no trained range model", index_name, run)
        return {}
    model, meta = loaded
    prev_close = float(fs.meta["prev_close"].iloc[0])
    ml = model.predict(fs.features)
    vix = VixNormalRange(model.targets, meta["bands"], meta["scale_column"]).predict(fs.features)
    out = {}
    for t in model.targets:
        source = "model" if meta["use_model"].get(t) else "vix_baseline"
        bands = (ml if source == "model" else vix)[t].iloc[0]
        name = t.removeprefix("y_")
        out[f"{name}_source"] = source
        for col, v in bands.items():
            out[f"{name}_{col}"] = round(prev_close * float(np.exp(v)), 2) if pd.notna(v) else None
        logger.info("%s %s %s (%s): median %s, 68%% [%s, %s], 95%% [%s, %s]", index_name, run, name,
                    source, out[f"{name}_med"], out[f"{name}_lo68"], out[f"{name}_hi68"],
                    out[f"{name}_lo95"], out[f"{name}_hi95"])
    return out


def predict_direction(cfg: dict, index_name: str, run: str, fs, target) -> dict | None:
    """P(up) for the live row using the saved model, or None if no model is trained yet."""
    loaded = load_artifact(artifact_path(cfg, "direction", index_name, run))
    if loaded is None:
        logger.warning("%s/%s: no trained direction model; run scripts/retrain.py", index_name, run)
        return None
    model, meta = loaded
    missing = [f for f in meta["features"] if f not in fs.features.columns]
    if missing:
        logger.warning("%s/%s: %d model features missing from the live row (treated as NaN): %s",
                       index_name, run, len(missing), missing[:8])
    p_up = float(model.predict_proba(fs.features)[0, 1])
    thr = float(cfg["models"]["direction"]["decision_threshold"])
    row_meta = fs.meta.iloc[0]
    if not meta.get("beats_baseline", False):
        logger.warning("%s/%s: this model did not beat the best baseline (%s) out of sample",
                       index_name, run, meta.get("best_baseline"))
    logger.info("%s %s: P(up)=%.3f -> %s | target=%s (%s) | data cutoff=%s, prev session=%s | "
                "model trained through %s", index_name, run, p_up, "UP" if p_up >= thr else "DOWN",
                target.target_date, target.label, row_meta["cutoff"].isoformat(),
                row_meta["prev_session"].date(), meta["trained_through"])
    return {
        "created_at": datetime.now(ist(cfg)).isoformat(),
        "target_date": target.target_date.isoformat(), "label": target.label,
        "index": index_name, "run": run, "p_up": round(p_up, 4),
        "call": "up" if p_up >= thr else "down", "decision_threshold": thr,
        "cutoff": row_meta["cutoff"].isoformat(),
        "prev_session": row_meta["prev_session"].date().isoformat(),
        "prev_close": float(row_meta["prev_close"]),
        "model_estimator": meta["estimator"], "model_trained_through": meta["trained_through"],
        "model_beats_baseline": bool(meta.get("beats_baseline", False)),
    }


def append_prediction(cfg: dict, record: dict) -> Path:
    """Append one prediction to the predictions log CSV (adding new columns if needed)."""
    path = resolve_path(cfg["data"]["processed_dir"]) / "predictions.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([record])
    if path.exists():
        old = pd.read_csv(path)
        if list(old.columns) != list(new.columns):
            pd.concat([old, new], ignore_index=True).to_csv(path, index=False)
            return path
    new.to_csv(path, mode="a", header=not path.exists(), index=False)
    return path


if __name__ == "__main__":
    sys.exit(main())
