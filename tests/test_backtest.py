"""Backtest cost model, simulation, metrics and timing tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.costs import CostModel
from backtest.strategy import (backtest_markdown, performance, positions_from_probability,
                               run_backtest, simulate)

IST = "Asia/Kolkata"


def costs(**kw):
    base = dict(brokerage_per_order=20, stt_sell_pct=0.02, exchange_txn_pct=0.00173,
                sebi_fee_pct=0.0001, stamp_duty_buy_pct=0.002, gst_pct=18, slippage_pct_per_side=0.0)
    return CostModel(**{**base, **kw})


def bars(opens, closes, start="2026-10-01"):
    idx = pd.bdate_range(start, periods=len(opens), tz=IST)
    return pd.DataFrame({"open": opens, "close": closes}, index=idx)


def test_cost_model_matches_hand_calculation():
    c = costs()
    buy, sell = np.array([24000 * 75.0]), np.array([24100 * 75.0])
    ch = c.charges(buy, sell)
    turnover = buy + sell
    assert ch["brokerage"][0] == 40
    assert ch["stt"][0] == pytest.approx(sell[0] * 0.0002)
    assert ch["stamp_duty"][0] == pytest.approx(buy[0] * 0.00002)
    assert ch["exchange"][0] == pytest.approx(turnover[0] * 0.0000173)
    assert ch["gst"][0] == pytest.approx(0.18 * (40 + turnover[0] * (0.0000173 + 0.000001)))
    assert ch["total"][0] == pytest.approx(sum(ch[k][0] for k in ("brokerage", "stt", "exchange",
                                                                   "sebi", "stamp_duty", "gst")))


def test_config_cost_model_loads(cfg):
    c = CostModel.from_config(cfg)
    assert c.stt_sell_pct > 0 and c.slippage_pct_per_side >= 0


def test_slippage_always_hurts():
    c = costs(slippage_pct_per_side=0.1)
    e, x = np.array([100.0, 100.0]), np.array([100.0, 100.0])
    fin, fout = c.fill_prices(e, x, np.array([1, -1]))
    assert fin[0] > 100 and fout[0] < 100   # long: buy high, sell low
    assert fin[1] < 100 and fout[1] > 100   # short: sell low, buy back high


def test_long_short_and_flat_returns():
    b = bars([100, 100, 100], [101, 99, 105])
    pos = pd.Series([1, -1, 0], index=b.index)
    gross = simulate(pos, b, None, lot_size=1)
    assert list(gross["gross_ret"].round(6)) == [0.01, 0.01, 0.0]
    net = simulate(pos, b, costs(), lot_size=75)
    assert (net["net_ret"].iloc[:2] < gross["gross_ret"].iloc[:2]).all()
    assert net["net_ret"].iloc[2] == 0 and net["cost_rs"].iloc[2] == 0


def test_round_trip_cost_in_bps_is_realistic(cfg):
    """With config costs, a flat Nifty round trip should cost a few basis points."""
    b = bars([24000.0], [24000.0])
    d = simulate(pd.Series([1], index=b.index), b, CostModel.from_config(cfg), lot_size=75)
    assert 2 < -d["net_ret"].iloc[0] * 1e4 < 10


def test_positions_from_probability():
    p = pd.Series([0.7, 0.5, 0.3, np.nan])
    assert list(positions_from_probability(p, 0.55, 0.45)) == [1, 0, -1, 0]
    assert list(positions_from_probability(p, 0.55, 0.45, allow_short=False)) == [1, 0, 0, 0]


def test_performance_known_values():
    idx = pd.bdate_range("2026-01-01", periods=4, tz=IST)
    r = pd.Series([0.1, -0.5, 0.0, 0.0], index=idx)
    m = performance(r, pd.Series([1, 1, 0, 0], index=idx), risk_free=0.0)
    assert m["total_return"] == pytest.approx(1.1 * 0.5 - 1)
    assert m["max_drawdown"] == pytest.approx(-0.5)
    assert m["n_trades"] == 2 and m["hit_rate"] == 0.5 and m["exposure"] == 0.5
    flat = performance(pd.Series(0.0, index=idx), pd.Series(0, index=idx))
    assert np.isnan(flat["sharpe_idle_cash_0"])  # never trades -> no Sharpe, not a huge number


def test_trade_on_day_d_only_uses_day_d_prices_and_forecast():
    """Changing the forecast for one session only changes that session's result, and
    results never depend on later prices."""
    b = bars([100, 101, 102, 103], [101, 100, 104, 102])
    pos = pd.Series([1, 1, 1, 1], index=b.index)
    base = simulate(pos, b, costs(), 75)
    pos2 = pos.copy()
    pos2.iloc[2] = -1
    alt = simulate(pos2, b, costs(), 75)
    changed = (base["net_ret"] != alt["net_ret"]).to_numpy()
    assert list(changed) == [False, False, True, False]
    b2 = b.copy()
    b2.iloc[3] = [500, 1]
    assert simulate(pos, b2, costs(), 75)["net_ret"].iloc[:3].equals(base["net_ret"].iloc[:3])


def test_run_backtest_end_to_end(cfg):
    rng = np.random.default_rng(0)
    n = 300
    close = 20000 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    open_ = close * np.exp(rng.normal(0, 0.003, n))
    b = bars(open_, close, start="2025-01-01")
    oos = pd.DataFrame({"y": 0, "p_model_lightgbm": rng.uniform(0.3, 0.7, n),
                        "p_baseline_always_up": 0.53, "p_baseline_previous_day": rng.uniform(0.4, 0.6, n)},
                       index=b.index)
    groups = {"vix_high": pd.Series(rng.random(n) > 0.7, index=b.index)}
    rep = run_backtest(oos, b, cfg, "nifty", "morning", groups)
    assert {"model", "model_gross", "always_long_intraday", "buy_and_hold",
            "model_prev_close_entry", "baseline_previous_day"} <= set(rep.strategies)
    assert not rep.strategies["model_prev_close_entry"].executable
    m, g = rep.strategies["model"].metrics, rep.strategies["model_gross"].metrics
    assert m["total_return"] < g["total_return"]  # costs reduce returns
    assert len(rep.threshold_grid) == len(cfg["backtest"]["threshold_grid"])
    md = backtest_markdown(rep)
    assert "NOT EXECUTABLE" in md and "Threshold sensitivity" in md and "vix_high" in md
