"""Feature builder tests (shape, run differences, cutoffs, optional inputs)."""

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from features.builder import build_features, nominal_cutoffs

IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture(scope="module")
def nifty_morning(market_bars, cfg, calendar):
    return build_features(market_bars, cfg, calendar, "nifty", "morning")


@pytest.fixture(scope="module")
def nifty_evening(market_bars, cfg, calendar):
    return build_features(market_bars, cfg, calendar, "nifty", "evening")


def test_rows_align_with_index_sessions(nifty_morning, market_bars):
    fs = nifty_morning
    assert len(fs.features) == len(market_bars["^NSEI"]) - 1
    assert fs.features.index.equals(fs.targets.index) and fs.features.index.equals(fs.meta.index)
    assert str(fs.features.index.tz) == "Asia/Kolkata"


def test_prev_close_is_previous_session_close(nifty_evening, market_bars):
    bars = market_bars["^NSEI"]
    expected = bars["close"].shift(1).reindex(nifty_evening.meta.index)
    pd.testing.assert_series_equal(nifty_evening.meta["prev_close"], expected, check_names=False)


def test_asian_features_only_in_morning(nifty_morning, nifty_evening):
    assert any(c.startswith("n225_") for c in nifty_morning.features)
    assert not any(c.startswith(("n225_", "hsi_")) for c in nifty_evening.features)


def test_us_session_used_per_run(nifty_morning, nifty_evening):
    d = pd.Timestamp("2026-11-04", tz=IST)  # Wednesday
    assert nifty_morning.meta.loc[d, "gspc_session"].date().isoformat() == "2026-11-03"
    assert nifty_evening.meta.loc[d, "gspc_session"].date().isoformat() == "2026-11-02"


def test_evening_cutoff_is_previous_session(nifty_evening):
    d = pd.Timestamp("2026-11-02", tz=IST)  # Monday
    assert nifty_evening.meta.loc[d, "cutoff"] == pd.Timestamp("2026-10-30 16:15", tz=IST)


def test_no_empty_feature_columns(nifty_morning):
    f = nifty_morning.features.iloc[300:]  # after warm-up
    allnan = [c for c in f if f[c].isna().all()]
    assert not allnan, allnan


def test_live_target_beyond_data(market_bars, cfg, calendar):
    now = datetime(2026, 11, 6, 16, 20, tzinfo=IST)
    target = pd.DatetimeIndex(["2026-11-09"], tz=IST)
    fs = build_features(market_bars, cfg, calendar, "nifty", "evening", target_dates=target,
                        cutoffs=pd.Series([pd.Timestamp(now)], index=target))
    assert fs.meta["prev_session"].iloc[0].date().isoformat() == "2026-11-06"
    assert fs.targets.iloc[0].isna().all()
    assert fs.features["idx_ret_1"].notna().all()


def test_stale_cue_becomes_missing(market_bars, cfg, calendar):
    bars = dict(market_bars)
    bars["^GSPC"] = bars["^GSPC"][bars["^GSPC"].index < pd.Timestamp("2026-10-01", tz=IST)]
    fs = build_features(bars, cfg, calendar, "nifty", "morning")
    late = fs.features.loc["2026-10-20":]
    assert late["gspc_ret_1"].isna().all()
    assert fs.features.loc["2026-09-15":"2026-09-30", "gspc_ret_1"].notna().all()


def test_missing_instrument_gives_nan_columns(market_bars, cfg, calendar):
    bars = {k: v for k, v in market_bars.items() if k != "BZ=F"}
    fs = build_features(bars, cfg, calendar, "nifty", "evening")
    assert fs.features["bz_f_ret_1"].isna().all()


def test_optional_gift_nifty_relative_and_morning_only(market_bars, cfg, calendar):
    idx = market_bars["^NSEI"].index[-30:]
    gift = pd.DataFrame({"price": market_bars["^NSEI"]["close"].iloc[-30:].to_numpy() * 1.01},
                        index=idx)
    gift["available_at"] = idx + pd.Timedelta(hours=8, minutes=30)
    opt = {"gift_nifty": gift}
    m = build_features(market_bars, cfg, calendar, "nifty", "morning", optional=opt)
    e = build_features(market_bars, cfg, calendar, "nifty", "evening", optional=opt)
    assert "opt_gift_nifty_price" in m.features and "opt_gift_nifty_price" not in e.features
    # Same-day 08:30 GIFT vs previous close; synthetic GIFT = same-day close * 1.01.
    d = idx[-1]
    expected = np.log(market_bars["^NSEI"].loc[d, "close"] * 1.01 / m.meta.loc[d, "prev_close"])
    assert m.features.loc[d, "opt_gift_nifty_price"] == pytest.approx(expected)


def test_bad_run_rejected(market_bars, cfg, calendar):
    with pytest.raises(ValueError):
        build_features(market_bars, cfg, calendar, "nifty", "midday")


def test_nominal_cutoffs_morning(market_bars, cfg):
    t = pd.DatetimeIndex(["2026-11-03"], tz=IST)
    assert nominal_cutoffs(t, market_bars["^NSEI"], "morning", cfg).iloc[0] == pd.Timestamp(
        "2026-11-03 08:45", tz=IST)
