"""Backtest the walk-forward direction forecasts as index-futures trades, after costs.

Needs the out-of-sample prediction files written by ``scripts/retrain.py``.

Usage:
    python scripts/backtest.py [--index nifty] [--run morning]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest.direction_eval import event_groups  # noqa: E402
from backtest.strategy import backtest_markdown, run_backtest  # noqa: E402
from data.calendar import TradingCalendar  # noqa: E402
from data.store import MarketDataStore  # noqa: E402
from features.builder import RUNS, build_dataset  # noqa: E402
from settings import load_config, resolve_path, setup_logging  # noqa: E402

logger = logging.getLogger("backtest")


def load_oos(path: Path, tz: str) -> pd.DataFrame:
    """Read an OOS predictions CSV with a tz-aware session-date index."""
    df = pd.read_csv(path, index_col=0)
    idx = pd.to_datetime(df.index, utc=True).tz_convert(tz).normalize()
    df.index = pd.DatetimeIndex(idx, name="session_date")
    return df


def main(argv: list[str] | None = None) -> int:
    """Run backtests and write reports. Returns 1 if any input was missing."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--index", help="only this index")
    parser.add_argument("--run", choices=RUNS, help="only this run")
    parser.add_argument("--config", help="path to config.yaml")
    args = parser.parse_args(argv)

    setup_logging()
    cfg = load_config(args.config)
    calendar = TradingCalendar.from_config(cfg)
    store = MarketDataStore(cfg)
    reports = resolve_path(cfg["reporting"]["reports_dir"])
    missing = 0
    for index_name in [args.index] if args.index else list(cfg["indices"]):
        bars = store.get(cfg["indices"][index_name]["ticker"])
        for run in [args.run] if args.run else RUNS:
            oos_path = reports / f"direction_{index_name}_{run}_oos.csv"
            if not oos_path.exists():
                logger.error("%s missing; run scripts/retrain.py first", oos_path)
                missing += 1
                continue
            oos = load_oos(oos_path, cfg["timezone"])
            fs = build_dataset(store, cfg, calendar, index_name, run, target_dates=oos.index)
            rep = run_backtest(oos, bars, cfg, index_name, run, event_groups(fs.features, cfg))
            tag = f"backtest_{index_name}_{run}"
            (reports / f"{tag}.md").write_text(backtest_markdown(rep))
            (reports / f"{tag}.json").write_text(json.dumps(
                {n: r.metrics for n, r in rep.strategies.items()} | {"warnings": rep.warnings},
                indent=2, default=float))
            rep.strategies["model"].daily.to_csv(reports / f"{tag}_trades.csv")
            m = rep.strategies["model"].metrics
            logger.info("%s: %d trades, hit %.1f%%, avg %.1f bps, CAGR %.1f%%, Sharpe(idle 0) %.2f, maxDD %.1f%%",
                        tag, m["n_trades"], m["hit_rate"] * 100, m["avg_trade_bps"], m["cagr"] * 100,
                        m["sharpe_idle_cash_0"], m["max_drawdown"] * 100)
            for w in rep.warnings:
                logger.warning("%s: %s", tag, w)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
