"""Unit tests for technical, event and target features."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from features.events import expiry_dates, event_features, session_days
from features.targets import build_targets
from features.technical import index_features, instrument_features, slug, vix_features


def test_slug():
    assert slug("^NSEI") == "nsei"
    assert slug("DX-Y.NYB") == "dx_y_nyb"
    assert slug("INR=X") == "inr_x"


def test_index_features_values(market_bars):
    bars = market_bars["^NSEI"]
    f = index_features(bars)
    c = bars["close"]
    assert f["ret_1"].iloc[10] == pytest.approx(np.log(c.iloc[10] / c.iloc[9]))
    assert f["gap"].iloc[10] == pytest.approx(np.log(bars["open"].iloc[10] / c.iloc[9]))
    assert f["rsi_14"].dropna().between(0, 100).all()
    assert f["close_pos"].dropna().between(0, 1).all()
    assert (f["available_at"] == bars["available_at"]).all()


def test_streak_counts_runs():
    from features.technical import _streak
    s = pd.Series([np.nan, 1, 2, -1, -1, -3, 4])
    assert list(_streak(s)) == [0, 1, 2, -1, -2, -3, 1]


def test_diff_transform_for_yields(market_bars):
    b = market_bars["^TNX"]
    f = instrument_features(b, "diff")
    assert f["ret_1"].iloc[5] == pytest.approx(b["close"].iloc[5] - b["close"].iloc[4])
    with pytest.raises(ValueError):
        instrument_features(b, "nope")


def test_vix_implied_move(market_bars):
    f = vix_features(market_bars["^INDIAVIX"])
    assert f["implied_move"].iloc[-1] == pytest.approx(f["level"].iloc[-1] / 100 / np.sqrt(252))
    assert f["pct_rank"].dropna().between(0, 1).all()


# ---------------------------------------------------------------- expiry

def nifty_expiries(cfg, calendar, start, end, name="nifty"):
    days = session_days([], calendar, start, end)
    return expiry_dates(cfg["indices"][name]["expiry_schedule"], days)


def test_nifty_nov_2026_weekly_tuesday_with_holiday_rollback(cfg, calendar):
    all_exp, monthly = nifty_expiries(cfg, calendar, date(2026, 11, 1), date(2026, 11, 30))
    # 10 Nov and 24 Nov are holidays -> expiry moves to Monday.
    assert sorted(all_exp) == [date(2026, 11, 3), date(2026, 11, 9), date(2026, 11, 17), date(2026, 11, 23)]
    assert monthly == {date(2026, 11, 23)}


def test_sensex_nov_2026_weekly_thursday(cfg, calendar):
    all_exp, monthly = nifty_expiries(cfg, calendar, date(2026, 11, 1), date(2026, 11, 30), "sensex")
    assert sorted(all_exp) == [date(2026, 11, 5), date(2026, 11, 12), date(2026, 11, 19), date(2026, 11, 26)]
    assert monthly == {date(2026, 11, 26)}


def test_nifty_switch_from_thursday_to_tuesday_in_sep_2025(cfg, calendar):
    all_exp, monthly = nifty_expiries(cfg, calendar, date(2025, 8, 18), date(2025, 9, 12))
    assert sorted(all_exp) == [date(2025, 8, 21), date(2025, 8, 28), date(2025, 9, 2), date(2025, 9, 9)]
    assert date(2025, 8, 28) in monthly


def test_monthly_only_era_uses_last_thursday():
    days = list(pd.bdate_range("2015-01-01", "2015-03-31").date)
    sched = [{"from": "2008-01-01", "frequency": "monthly", "weekday": "Thursday"}]
    all_exp, monthly = expiry_dates(sched, days)
    assert sorted(all_exp) == [date(2015, 1, 29), date(2015, 2, 26), date(2015, 3, 26)]
    assert all_exp == monthly


def test_session_days_uses_data_for_uncovered_years(calendar):
    data_days = [date(2015, 1, 1), date(2015, 1, 5)]  # pretend 2 Jan was a holiday
    assert session_days(data_days, calendar, date(2015, 1, 1), date(2015, 1, 5)) == data_days


# ---------------------------------------------------------------- events

def ev(cfg, calendar, dates, name="nifty", index_dates=()):
    idx = pd.DatetimeIndex(dates).tz_localize("Asia/Kolkata")
    return event_features(idx, cfg, calendar, name, list(index_dates))


def test_event_flags_and_coverage(cfg, calendar):
    f = ev(cfg, calendar, ["2024-06-04", "2024-06-05", "2025-12-05", "2026-11-03"])
    assert list(f["is_election_results"]) == [1.0, 0.0, 0.0, 0.0]
    assert f.loc["2025-12-05", "is_rbi_policy"].item() == 1.0
    assert np.isnan(f.loc["2026-11-03", "is_rbi_policy"].item())  # outside RBI coverage


def test_weekend_event_maps_to_next_session(cfg, calendar):
    # 2009 isn't in the holiday calendar, so supply the sessions from "data".
    days = list(pd.bdate_range("2009-05-01", "2009-06-30").date)
    f = ev(cfg, calendar, ["2009-05-15", "2009-05-18"], index_dates=days)
    assert list(f["is_election_results"]) == [0.0, 1.0]  # Saturday 16 May -> Monday


def test_expiry_and_gap_features_around_diwali_2026(cfg, calendar):
    f = ev(cfg, calendar, ["2026-11-04", "2026-11-09", "2026-11-11"])
    assert f.loc["2026-11-04", "sessions_to_expiry"].item() == 3.0   # Wed -> Mon 9 Nov
    assert f.loc["2026-11-09", "is_expiry"].item() == 1.0
    assert f.loc["2026-11-09", "days_to_next_session"].item() == 2.0  # Tue 10 Nov holiday
    assert f.loc["2026-11-09", "after_muhurat"].item() == 1.0         # Sunday 8 Nov Muhurat
    assert f.loc["2026-11-11", "days_since_prev_session"].item() == 2.0
    assert f.loc["2026-11-04", "is_results_season"].item() == 1.0


# ---------------------------------------------------------------- targets

def test_targets(cfg):
    idx = pd.DatetimeIndex(["2026-11-02", "2026-11-03", "2026-11-04"], tz="Asia/Kolkata")
    bars = pd.DataFrame({"open": [100, 100.1, 99.0], "high": [101, 102, 100],
                         "low": [99, 99.5, 98], "close": [100, 101, 99.5]}, index=idx)
    prev = pd.Series([np.nan, 100.0, 101.0], index=idx)
    live = pd.Timestamp("2026-11-05", tz="Asia/Kolkata")
    prev = pd.concat([prev, pd.Series([99.5], index=[live])])
    t = build_targets(bars, prev, cfg)
    assert t.loc[idx[1], "y_direction"] == 1.0
    assert t.loc[idx[1], "y_gap"] == 0.0             # +0.1% is within the flat band
    assert t.loc[idx[2], "y_gap"] == -1.0            # -1.98%
    assert t.loc[idx[1], "y_high"] == pytest.approx(np.log(102 / 100))
    assert t.loc[live].isna().all()                  # no bar yet for a live target
