"""Look-ahead bias tests. NEVER weaken or skip these.

Data layer: availability timestamps and the as-of filter.
Feature layer: for each target session, features built from the full history must
equal features built from only the data available before the cutoff, and must not
change when future data (including the target session's own bar) is altered.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from data.optional_inputs import load_optional_input
from data.store import MarketDataStore, available_as_of
from features.builder import build_features
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


# ---------------------------------------------------------------- feature level

CASES = [(i, r) for i in ("nifty", "sensex") for r in ("morning", "evening")]
# Ordinary days, a Monday, the session after the Diwali 2025 holidays, an expiry day,
# and the last session in the data.
SAMPLE_DATES = ["2025-03-12", "2025-06-30", "2025-10-23", "2026-11-03", "2026-11-06"]


def _row_equal(a: pd.Series, b: pd.Series) -> None:
    pd.testing.assert_series_equal(a, b, check_names=False, rtol=1e-12, atol=0)


@pytest.fixture(scope="module")
def full_builds(market_bars, cfg, calendar):
    return {c: build_features(market_bars, cfg, calendar, *c) for c in CASES}


@pytest.mark.parametrize("case", CASES)
def test_features_equal_when_built_from_only_past_data(case, full_builds, market_bars, cfg, calendar):
    full = full_builds[case]
    for d in SAMPLE_DATES:
        d = pd.Timestamp(d, tz=IST)
        cutoff = full.meta.loc[d, "cutoff"]
        past_only = {t: available_as_of(df, cutoff) for t, df in market_bars.items()}
        target = pd.DatetimeIndex([d])
        trunc = build_features(past_only, cfg, calendar, *case, target_dates=target,
                               cutoffs=pd.Series([cutoff], index=target))
        _row_equal(trunc.features.loc[d], full.features.loc[d])
        assert trunc.meta.loc[d, "prev_close"] == full.meta.loc[d, "prev_close"]


@pytest.mark.parametrize("case", CASES)
def test_features_unchanged_when_future_data_is_tampered(case, full_builds, market_bars, cfg, calendar):
    full = full_builds[case]
    rng = np.random.default_rng(7)
    for d in SAMPLE_DATES[:-1]:
        d = pd.Timestamp(d, tz=IST)
        cutoff = full.meta.loc[d, "cutoff"]
        tampered = {}
        for t, df in market_bars.items():
            df = df.copy()
            future = (df["available_at"] >= cutoff).to_numpy()
            noise = rng.uniform(0.7, 1.3, size=(int(future.sum()), 1))
            df.loc[future, ["open", "high", "low", "close"]] *= noise
            tampered[t] = df
        rebuilt = build_features(tampered, cfg, calendar, *case)
        _row_equal(rebuilt.features.loc[d], full.features.loc[d])
        # The target itself does depend on the tampered session bar.
        assert rebuilt.targets.loc[d, "y_close"] != full.targets.loc[d, "y_close"]


@pytest.mark.parametrize("case", CASES)
def test_no_feature_correlates_with_same_day_outcome(case, full_builds):
    """Canary: synthetic series are independent random walks, so no honest feature can
    predict the target's close-to-close return. A strong correlation means a leak."""
    fs = full_builds[case]
    y = fs.targets["y_close"]
    corr = fs.features.iloc[60:].corrwith(y.iloc[60:]).abs().dropna()
    assert (corr < 0.2).all(), corr[corr >= 0.2].to_dict()
