"""Look-ahead bias tests. NEVER weaken or skip these.

Stage 1 covers the data layer: availability timestamps and the as-of filter.
Feature-level leakage tests (shift future data, features must not change) are
added here with the features stage.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from data.optional_inputs import load_optional_input
from data.store import MarketDataStore, available_as_of
from tests.conftest import FakeSource, make_bars

IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def store(cfg, tmp_path):
    c = dict(cfg)
    c["data"] = dict(cfg["data"], history_start="2026-06-01")
    dates = pd.bdate_range("2026-06-01", "2026-11-06")
    src = FakeSource({t: make_bars(dates, seed=i) for i, t in enumerate(cfg["instruments"])})
    # "now" is far in the future so every bar is cached; the tests apply cutoffs.
    s = MarketDataStore(c, source=src, cache_dir=tmp_path,
                        now_fn=lambda: datetime(2026, 12, 31, tzinfo=IST))
    s.update_all()
    return s


def test_us_close_only_available_to_next_indian_session(store):
    spx = store.get("^GSPC")
    # Morning run on Tue 3 Nov: Monday 2 Nov US close (02:30 IST + delay) is known,
    # Tuesday 3 Nov US session is not.
    seen = available_as_of(spx, datetime(2026, 11, 3, 8, 45, tzinfo=IST))
    assert seen.index.max().date().isoformat() == "2026-11-02"
    # Evening run on Tue 3 Nov: still only Monday's US close.
    seen = available_as_of(spx, datetime(2026, 11, 3, 16, 15, tzinfo=IST))
    assert seen.index.max().date().isoformat() == "2026-11-02"


def test_indian_close_not_available_before_close(store):
    nifty = store.get("^NSEI")
    assert available_as_of(nifty, datetime(2026, 11, 3, 15, 30, tzinfo=IST)).index.max().day == 2
    assert available_as_of(nifty, datetime(2026, 11, 3, 16, 15, tzinfo=IST)).index.max().day == 3


def test_asian_close_not_available_in_morning_run(store):
    nikkei = store.get("^N225")
    seen = available_as_of(nikkei, datetime(2026, 11, 3, 8, 45, tzinfo=IST))
    assert seen.index.max().day == 2  # same-day Nikkei closes at 12:00 IST


def test_every_bar_available_after_its_session_date(store, cfg):
    # No instrument may become available before its own session date starts (IST).
    for ticker in cfg["instruments"]:
        df = store.get(ticker)
        assert (df["available_at"] > df.index).all(), ticker


def test_as_of_filter_ignores_future_rows(store, cfg):
    """Appending or changing future data must not change what is visible at a cutoff."""
    cutoff = datetime(2026, 10, 15, 8, 45, tzinfo=IST)
    for ticker in cfg["instruments"]:
        df = store.get(ticker)
        before = available_as_of(df, cutoff)
        future = df["available_at"] >= pd.Timestamp(cutoff)
        tampered = df.copy()
        tampered.loc[future, ["open", "high", "low", "close"]] *= np.random.default_rng(1).uniform(
            0.5, 1.5, size=(int(future.sum()), 1))
        extra = tampered.tail(1).copy()
        extra.index = extra.index + timedelta(days=30)
        extra["available_at"] = extra["available_at"] + timedelta(days=30)
        tampered = pd.concat([tampered, extra])
        pd.testing.assert_frame_equal(available_as_of(tampered, cutoff), before)


def test_naive_cutoff_rejected(store):
    with pytest.raises(ValueError):
        available_as_of(store.get("^NSEI"), datetime(2026, 11, 3, 8, 45))


def test_optional_input_respects_release_time(cfg, tmp_path):
    path = tmp_path / "fii.csv"
    path.write_text("date,fii_net\n2026-11-02,-1200\n2026-11-03,850\n")
    c = dict(cfg, optional_inputs={"fii_dii": {"path": str(path), "date_column": "date",
                                               "available_time": "20:00"}})
    df = load_optional_input("fii_dii", c)
    # The 3 Nov figure isn't out at the 16:15 evening run, only after 20:00.
    assert available_as_of(df, datetime(2026, 11, 3, 16, 15, tzinfo=IST)).index.max().day == 2
    assert available_as_of(df, datetime(2026, 11, 3, 20, 30, tzinfo=IST)).index.max().day == 3
