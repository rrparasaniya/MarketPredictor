"""Prediction target timing tests (Asia/Kolkata)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from data.timing import PredictionMode, resolve_prediction_target

IST = ZoneInfo("Asia/Kolkata")


def at(y, m, d, hh, mm, tz=IST):
    return datetime(y, m, d, hh, mm, tzinfo=tz)


def test_before_open_predicts_today(calendar, cfg):
    t = resolve_prediction_target(at(2026, 11, 3, 8, 45), calendar, cfg)
    assert (t.target_date, t.mode, t.label, t.generate_new) == (
        date(2026, 11, 3), PredictionMode.PRE_OPEN, "today", True)


def test_market_hours_shows_existing_prediction(calendar, cfg):
    for hh, mm in [(9, 15), (12, 0), (15, 29)]:
        t = resolve_prediction_target(at(2026, 11, 3, hh, mm), calendar, cfg)
        assert t.mode is PredictionMode.INTRADAY
        assert t.target_date == date(2026, 11, 3)
        assert not t.generate_new


def test_after_close_predicts_next_session(calendar, cfg):
    t = resolve_prediction_target(at(2026, 11, 3, 15, 30), calendar, cfg)
    assert (t.target_date, t.mode, t.label) == (date(2026, 11, 4), PredictionMode.POST_CLOSE, "tomorrow")


def test_friday_evening_predicts_monday(calendar, cfg):
    t = resolve_prediction_target(at(2026, 11, 6, 16, 15), calendar, cfg)
    assert (t.target_date, t.label) == (date(2026, 11, 9), "next session")


def test_evening_before_holiday_skips_it(calendar, cfg):
    t = resolve_prediction_target(at(2026, 11, 9, 16, 15), calendar, cfg)
    assert t.target_date == date(2026, 11, 11)


def test_morning_of_holiday_predicts_next_session(calendar, cfg):
    t = resolve_prediction_target(at(2026, 11, 10, 8, 45), calendar, cfg)
    assert (t.target_date, t.mode) == (date(2026, 11, 11), PredictionMode.NON_TRADING_DAY)


def test_other_timezones_are_converted_to_ist(calendar, cfg):
    # 03:00 UTC = 08:30 IST, before the open
    t = resolve_prediction_target(at(2026, 11, 3, 3, 0, ZoneInfo("UTC")), calendar, cfg)
    assert t.mode is PredictionMode.PRE_OPEN
    assert t.as_of.utcoffset().total_seconds() == 5.5 * 3600


def test_naive_time_rejected(calendar, cfg):
    with pytest.raises(ValueError):
        resolve_prediction_target(datetime(2026, 11, 3, 8, 45), calendar, cfg)
