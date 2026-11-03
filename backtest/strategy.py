"""Turn next-session P(up) forecasts into futures trades and measure them after costs.

Timing: the forecast for session D exists before D opens (morning run at 08:45, or the
evening run after the previous close). The first tradable price is D's open, so every
trade enters at D's open and exits at D's close. The forecast never sees D's prices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from backtest.costs import CostModel

TRADING_DAYS = 252


def positions_from_probability(p: pd.Series, long_thr: float, short_thr: float,
                               allow_short: bool = True) -> pd.Series:
    """+1 long, -1 short, 0 flat for each session (NaN probabilities -> flat)."""
    pos = pd.Series(0, index=p.index, dtype=int)
    pos[p >= long_thr] = 1
    if allow_short:
        pos[p <= short_thr] = -1
    return pos


def simulate(positions: pd.Series, bars: pd.DataFrame, costs: CostModel | None,
             lot_size: float, lots: int = 1, entry_col: str = "open",
             exit_col: str = "close") -> pd.DataFrame:
    """Daily trade results for given positions.

    Args:
        positions: +1/-1/0 per target session.
        bars: Index bars with ``entry_col`` and ``exit_col`` (session-date index).
        costs: Cost model, or None for gross (frictionless) results.
        lot_size: Units per lot.
        lots: Lots per trade.
        entry_col / exit_col: Price columns to trade at.

    Returns:
        Per session: position, entry/exit prices, gross and net return (fraction of
        entry notional), cost in rupees and in return terms. Flat days return 0.
    """
    px = bars.reindex(positions.index)
    entry, exit_ = px[entry_col].to_numpy(float), px[exit_col].to_numpy(float)
    side = positions.to_numpy(int)
    traded = (side != 0) & np.isfinite(entry) & np.isfinite(exit_)
    gross = np.where(traded, side * (exit_ / entry - 1), 0.0)
    out = pd.DataFrame({"position": np.where(traded, side, 0), "entry": entry, "exit": exit_,
                        "gross_ret": gross}, index=positions.index)
    if costs is None:
        out["cost_rs"] = 0.0
        out["net_ret"] = gross
        return out
    qty = lot_size * lots
    s = np.where(side == 0, 1, side)
    fill_in, fill_out = costs.fill_prices(entry, exit_, s)
    buy_px = np.where(s > 0, fill_in, fill_out)
    sell_px = np.where(s > 0, fill_out, fill_in)
    ch = costs.charges(buy_px * qty, sell_px * qty)
    notional = entry * qty
    net_pnl = (sell_px - buy_px) * qty - ch["total"]
    out["cost_rs"] = np.where(traded, ch["total"], 0.0)
    out["net_ret"] = np.where(traded, net_pnl / notional, 0.0)
    return out


def performance(daily_ret: pd.Series, positions: pd.Series | None = None,
                risk_free: float = 0.065) -> dict[str, float]:
    """Return statistics for a daily return series (fractions of capital).

    Two Sharpe ratios are reported: one where idle capital earns nothing (excess return
    = r - rf/252, the conservative default), and one where the capital sits in cash
    earning the risk-free rate (excess = r).
    """
    r = daily_ret.fillna(0.0).to_numpy(float)
    n = len(r)
    if n == 0:
        return {"days": 0}
    equity = np.cumprod(1 + r)
    years = n / TRADING_DAYS
    peak = np.maximum.accumulate(equity)
    rf_d = risk_free / TRADING_DAYS

    flat = np.allclose(r, r[0])  # e.g. a strategy that never trades

    def sharpe(x: np.ndarray) -> float:
        sd = x.std(ddof=1)
        return float(x.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 0 and not flat else float("nan")

    out = {
        "days": n,
        "total_return": float(equity[-1] - 1),
        "cagr": float(equity[-1] ** (1 / years) - 1) if equity[-1] > 0 else -1.0,
        "ann_vol": float(r.std(ddof=1) * np.sqrt(TRADING_DAYS)),
        "sharpe_idle_cash_0": sharpe(r - rf_d),
        "sharpe_idle_cash_rf": sharpe(r),
        "max_drawdown": float((equity / peak - 1).min()),
    }
    if positions is not None:
        pos = positions.reindex(daily_ret.index).fillna(0).to_numpy()
        trades = r[pos != 0]
        out.update({
            "n_trades": int((pos != 0).sum()),
            "exposure": float((pos != 0).mean()),
            "long_share": float((pos > 0).sum() / max((pos != 0).sum(), 1)),
            "hit_rate": float((trades > 0).mean()) if len(trades) else float("nan"),
            "avg_trade_bps": float(trades.mean() * 1e4) if len(trades) else float("nan"),
        })
    return out


@dataclass
class StrategyResult:
    """Simulated daily results and performance for one named strategy."""

    name: str
    daily: pd.DataFrame
    metrics: dict[str, float]
    executable: bool = True
    note: str = ""


@dataclass
class BacktestReport:
    """All strategies for one index and run, plus breakdowns."""

    index_name: str
    run: str
    strategies: dict[str, StrategyResult]
    threshold_grid: pd.DataFrame
    by_year: pd.DataFrame
    by_subset: pd.DataFrame
    warnings: list[str] = field(default_factory=list)


def run_backtest(oos: pd.DataFrame, bars: pd.DataFrame, cfg: dict[str, Any], index_name: str,
                 run: str, groups: dict[str, pd.Series] | None = None) -> BacktestReport:
    """Backtest the model and baseline signals from walk-forward OOS predictions.

    Args:
        oos: Out-of-sample predictions (``p_model_*``, ``p_baseline_*`` columns) indexed by
            target session date (tz-aware IST).
        bars: The index's daily bars.
        cfg: Project config.
        index_name: ``nifty`` or ``sensex`` (for the lot size).
        run: ``morning`` or ``evening`` (labels only).
        groups: Optional boolean masks (VIX regime, event days) for breakdowns.
    """
    b = cfg["backtest"]
    costs = CostModel.from_config(cfg)
    lot = float(b["lot_size"][index_name])
    lots = int(b.get("lots", 1))
    rf = float(b["risk_free_rate"])
    lt, st, short = float(b["long_threshold"]), float(b["short_threshold"]), bool(b["allow_short"])
    idx = oos.index
    model_col = b["model_column"]
    if model_col not in oos:
        raise KeyError(f"{model_col} not in OOS predictions; columns: {list(oos.columns)}")

    def strat(name: str, pos: pd.Series, cost: CostModel | None = costs, entry: str = "open",
              executable: bool = True, note: str = "") -> StrategyResult:
        daily = simulate(pos, bars, cost, lot, lots, entry_col=entry)
        return StrategyResult(name, daily, performance(daily["net_ret"], daily["position"], rf),
                              executable, note)

    res: dict[str, StrategyResult] = {}
    model_pos = positions_from_probability(oos[model_col], lt, st, short)
    res["model"] = strat("model", model_pos, note=f"{model_col}: long >= {lt}, short <= {st}")
    res["model_gross"] = strat("model_gross", model_pos, cost=None, note="same trades, no costs")
    for col in [c for c in oos.columns if c.startswith("p_baseline_")]:
        name = col.removeprefix("p_")
        res[name] = strat(name, positions_from_probability(oos[col], lt, st, short))
    res["always_long_intraday"] = strat("always_long_intraday", pd.Series(1, index=idx),
                                        note="long every session open -> close")
    # Buy and hold the index close to close (frictionless reference).
    bh = bars["close"].pct_change().reindex(idx).fillna(0.0)
    res["buy_and_hold"] = StrategyResult(
        "buy_and_hold", pd.DataFrame({"position": 1, "net_ret": bh, "gross_ret": bh}, index=idx),
        performance(bh, None, rf), note="index close to close, no costs")
    # Not executable: entering at the previous close needs the forecast before 15:30.
    prev = bars[["close"]].copy()
    prev["prev_close"] = prev["close"].shift(1)
    res["model_prev_close_entry"] = StrategyResult(
        "model_prev_close_entry",
        (d := simulate(model_pos, prev, None, lot, lots, entry_col="prev_close")),
        performance(d["net_ret"], d["position"], rf), executable=False,
        note="NOT EXECUTABLE: enters at the previous close, before the forecast exists. "
             "Shows how much of the edge is the overnight gap.")

    grid = []
    for thr in b.get("threshold_grid", []):
        pos = positions_from_probability(oos[model_col], thr, 1 - thr, short)
        m = performance(simulate(pos, bars, costs, lot, lots)["net_ret"], pos, rf)
        grid.append({"long_threshold": thr, "short_threshold": round(1 - thr, 4), **m})
    grid_df = pd.DataFrame(grid)

    years = pd.DataFrame({n: r.daily["net_ret"].groupby(r.daily.index.year).apply(
        lambda x: float(np.prod(1 + x) - 1)) for n, r in res.items()
        if n in ("model", "model_gross", "always_long_intraday", "buy_and_hold")})

    subset_rows = []
    for g, mask in (groups or {}).items():
        m = mask.reindex(idx).fillna(False).astype(bool)
        d = res["model"].daily[m.to_numpy()]
        t = d[d["position"] != 0]
        subset_rows.append({"subset": g, "sessions": int(m.sum()), "trades": len(t),
                            "hit_rate": float((t["net_ret"] > 0).mean()) if len(t) else np.nan,
                            "avg_trade_net_bps": float(t["net_ret"].mean() * 1e4) if len(t) else np.nan,
                            "avg_trade_gross_bps": float(t["gross_ret"].mean() * 1e4) if len(t) else np.nan})
    warnings = []
    if res["model"].metrics.get("sharpe_idle_cash_0", np.nan) <= res["always_long_intraday"].metrics.get(
            "sharpe_idle_cash_0", np.nan):
        warnings.append("The model strategy does not beat always-long intraday after costs.")
    if res["model"].metrics["total_return"] <= 0:
        warnings.append("The model strategy loses money after costs over the test period.")
    return BacktestReport(index_name, run, res, grid_df, years, pd.DataFrame(subset_rows), warnings)


def backtest_markdown(rep: BacktestReport) -> str:
    """Human-readable backtest report."""
    first = next(iter(rep.strategies.values())).daily.index
    lines = [f"## Backtest: {rep.index_name} ({rep.run} run)", "",
             f"Out-of-sample {first.min().date()} to {first.max().date()} ({len(first)} sessions). "
             "Trades enter at the target session's open and exit at its close, on index prices as a "
             "stand-in for futures. Net of brokerage, STT, exchange charges, SEBI fee, GST, stamp duty "
             "and slippage. Sharpe uses a 6.5% risk-free rate; 'idle cash 0' assumes unused capital "
             "earns nothing (conservative), 'idle cash rf' assumes it earns the risk-free rate.", "",
             "| strategy | trades | exposure | hit rate | avg trade bps | total return | CAGR | "
             "ann vol | Sharpe (idle cash 0) | Sharpe (idle cash rf) | max DD |",
             "|---" * 11 + "|"]

    def f(v: Any, pct: bool = False, d: int = 2) -> str:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "—"
        return f"{v * 100:.1f}%" if pct else f"{v:.{d}f}"

    for name, r in rep.strategies.items():
        m = r.metrics
        label = name if r.executable else f"{name} ⚠"
        lines.append(f"| {label} | {m.get('n_trades', '—')} | {f(m.get('exposure'), True)} | "
                     f"{f(m.get('hit_rate'), True)} | {f(m.get('avg_trade_bps'), d=1)} | "
                     f"{f(m['total_return'], True)} | {f(m['cagr'], True)} | {f(m['ann_vol'], True)} | "
                     f"{f(m['sharpe_idle_cash_0'])} | {f(m['sharpe_idle_cash_rf'])} | "
                     f"{f(m['max_drawdown'], True)} |")
    lines += [""] + [f"- `{n}`: {r.note}" for n, r in rep.strategies.items() if r.note]
    if not rep.threshold_grid.empty:
        lines += ["", "### Threshold sensitivity (model, net)", "",
                  "| long ≥ / short ≤ | trades | hit rate | avg trade bps | CAGR | Sharpe (idle cash 0) | max DD |",
                  "|---" * 7 + "|"]
        for _, g in rep.threshold_grid.iterrows():
            lines.append(f"| {g['long_threshold']:.2f} / {g['short_threshold']:.2f} | {int(g['n_trades'])} | "
                         f"{f(g['hit_rate'], True)} | {f(g['avg_trade_bps'], d=1)} | {f(g['cagr'], True)} | "
                         f"{f(g['sharpe_idle_cash_0'])} | {f(g['max_drawdown'], True)} |")
    if not rep.by_subset.empty:
        lines += ["", "### Model trades by regime and event", "",
                  "| subset | sessions | trades | hit rate | avg net bps | avg gross bps |", "|---" * 6 + "|"]
        for _, s in rep.by_subset.iterrows():
            lines.append(f"| {s['subset']} | {s['sessions']} | {s['trades']} | {f(s['hit_rate'], True)} | "
                         f"{f(s['avg_trade_net_bps'], d=1)} | {f(s['avg_trade_gross_bps'], d=1)} |")
    lines += ["", "### Return by year", "", "| year | " + " | ".join(rep.by_year.columns) + " |",
              "|---" * (len(rep.by_year.columns) + 1) + "|"]
    for y, row in rep.by_year.iterrows():
        lines.append(f"| {y} | " + " | ".join(f(v, True) for v in row) + " |")
    if rep.warnings:
        lines += ["", "### Warnings", ""] + [f"- {w}" for w in rep.warnings]
    return "\n".join(lines) + "\n"
