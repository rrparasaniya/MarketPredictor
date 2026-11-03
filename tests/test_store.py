"""Market data store tests: caching, incremental updates, failures, availability."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from data.store import MarketDataStore, compute_available_at, validate_bars
from tests.conftest import FakeSource, make_bars

IST = ZoneInfo("Asia/Kolkata")


def bdays(start, end):
    return pd.bdate_range(start, end)


@pytest.fixture
def small_cfg(cfg):
    c = dict(cfg)
    c["data"] = dict(cfg["data"], history_start="2026-09-01")
    c["instruments"] = {k: cfg["instruments"][k] for k in ("^NSEI", "^GSPC")}
    c["indices"] = {"nifty": cfg["indices"]["nifty"]}
    return c


def make_store(cfg, tmp_path, source, now):
    return MarketDataStore(cfg, source=source, cache_dir=tmp_path, now_fn=lambda: now)


def test_available_at_for_nse_bar(cfg):
    avail = compute_available_at(pd.DatetimeIndex(["2026-11-03"]), "Asia/Kolkata", "15:30",
                                 "Asia/Kolkata", 15)
    assert avail[0] == pd.Timestamp("2026-11-03 15:45", tz=IST)


def test_available_at_for_us_bar_handles_dst():
    # US summer (EDT): 16:00 NY = 01:30 IST next day; winter (EST): 02:30 IST.
    avail = compute_available_at(pd.DatetimeIndex(["2026-07-15", "2026-12-15"]),
                                 "America/New_York", "16:00", "Asia/Kolkata", 0)
    assert avail[0] == pd.Timestamp("2026-07-16 01:30", tz=IST)
    assert avail[1] == pd.Timestamp("2026-12-16 02:30", tz=IST)


def test_first_update_downloads_history_and_caches(small_cfg, tmp_path):
    src = FakeSource({"^NSEI": make_bars(bdays("2026-09-01", "2026-11-02"))})
    now = datetime(2026, 11, 3, 8, 45, tzinfo=IST)
    store = make_store(small_cfg, tmp_path, src, now)
    res = store.update("^NSEI")
    assert res.ok and res.last_session == date(2026, 11, 2)
    assert src.calls[0][1] == date(2026, 9, 1)
    df = store.get("^NSEI")
    assert len(src.calls) == 1  # get() served from cache
    assert str(df.index.tz) == "Asia/Kolkata"
    assert df["available_at"].dt.tz is not None


def test_incremental_update_only_fetches_recent_days(small_cfg, tmp_path):
    full = make_bars(bdays("2026-09-01", "2026-11-03"))
    src = FakeSource({"^NSEI": full[full.index <= "2026-10-30"]})
    store = make_store(small_cfg, tmp_path, src, datetime(2026, 10, 31, 9, 0, tzinfo=IST))
    store.update("^NSEI")
    src.data["^NSEI"] = full
    store.now_fn = lambda: datetime(2026, 11, 3, 16, 30, tzinfo=IST)
    res = store.update("^NSEI")
    assert src.calls[1][1] == date(2026, 10, 23)  # last cached date minus 7-day overlap
    assert res.last_session == date(2026, 11, 3)
    pd.testing.assert_frame_equal(store.get("^NSEI")[full.columns].reset_index(drop=True),
                                  full.reset_index(drop=True))


def test_unfinished_bar_is_not_cached(small_cfg, tmp_path):
    src = FakeSource({"^NSEI": make_bars(bdays("2026-10-01", "2026-11-03"))})
    store = make_store(small_cfg, tmp_path, src, datetime(2026, 11, 3, 11, 0, tzinfo=IST))
    res = store.update("^NSEI")
    assert res.last_session == date(2026, 11, 2)  # today's in-progress bar dropped


def test_fetch_failure_keeps_cache(small_cfg, tmp_path):
    src = FakeSource({"^NSEI": make_bars(bdays("2026-09-01", "2026-10-30"))})
    store = make_store(small_cfg, tmp_path, src, datetime(2026, 11, 2, 9, 0, tzinfo=IST))
    store.update("^NSEI")
    src.fail = True
    res = store.update("^NSEI")
    assert not res.ok and res.rows > 0 and "keeping" in res.message
    assert len(store.get("^NSEI")) == res.rows


def test_failure_with_empty_cache_returns_empty_frame(small_cfg, tmp_path):
    src = FakeSource({})
    src.fail = True
    store = make_store(small_cfg, tmp_path, src, datetime(2026, 11, 3, 9, 0, tzinfo=IST))
    df = store.get("^NSEI")
    assert df.empty and "available_at" in df.columns


def test_update_all_continues_after_one_failure(small_cfg, tmp_path):
    src = FakeSource({"^NSEI": make_bars(bdays("2026-09-01", "2026-10-30"))})  # ^GSPC missing -> KeyError
    store = make_store(small_cfg, tmp_path, src, datetime(2026, 11, 2, 9, 0, tzinfo=IST))
    results = {r.ticker: r for r in store.update_all()}
    assert results["^NSEI"].ok and not results["^GSPC"].ok


def test_unconfigured_ticker_rejected(small_cfg, tmp_path):
    store = make_store(small_cfg, tmp_path, FakeSource({}), datetime(2026, 11, 3, 9, 0, tzinfo=IST))
    with pytest.raises(KeyError):
        store.update("^FOO")


def test_validate_bars_flags_bad_rows():
    df = make_bars(bdays("2026-10-01", "2026-10-10"))
    df.iloc[2, df.columns.get_loc("high")] = df.iloc[2]["close"] * 0.9
    df.iloc[3, df.columns.get_loc("close")] = -1
    issues = validate_bars(df, "TEST")
    assert any("high below" in i for i in issues)
    assert any("non-positive" in i for i in issues)
    assert validate_bars(make_bars(bdays("2026-10-01", "2026-10-10")), "OK") == []
