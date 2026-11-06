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


# ---------------------------------------------------------------- model choice and stale inputs

from data.timing import expected_prev_session, inputs_are_current, run_for_target  # noqa: E402


@pytest.mark.parametrize("hh,mm,run", [(0, 1, "evening"), (3, 59, "evening"), (4, 0, "morning"),
                                       (8, 30, "morning")])
def test_pre_open_run_uses_morning_models_only_once_us_data_is_in(calendar, cfg, hh, mm, run):
    t = resolve_prediction_target(at(2026, 11, 5, hh, mm), calendar, cfg)
    assert t.mode is PredictionMode.PRE_OPEN
    assert run_for_target(t, cfg) == run


def test_post_close_and_non_trading_runs_use_evening_models(calendar, cfg):
    assert run_for_target(resolve_prediction_target(at(2026, 11, 5, 16, 15), calendar, cfg), cfg) == "evening"
    assert run_for_target(resolve_prediction_target(at(2026, 11, 7, 10, 0), calendar, cfg), cfg) == "evening"


def test_inputs_current_rejects_a_skipped_session(calendar):
    # 15:31 on 5 Nov: today's bar isn't final, so the latest bar is 4 Nov.
    assert not inputs_are_current(date(2026, 11, 4), date(2026, 11, 6), calendar)
    assert inputs_are_current(date(2026, 11, 5), date(2026, 11, 6), calendar)


def test_inputs_current_across_weekends_holidays_and_special_sessions(calendar):
    assert inputs_are_current(date(2026, 11, 6), date(2026, 11, 9), calendar)    # Fri -> Mon
    assert inputs_are_current(date(2026, 11, 9), date(2026, 11, 11), calendar)   # 10 Nov holiday
    # Sunday 1 Feb 2026 Budget session often has no Yahoo bar: Friday's bar is current.
    assert expected_prev_session(date(2026, 2, 2), calendar) == date(2026, 1, 30)
    assert inputs_are_current(date(2026, 1, 30), date(2026, 2, 2), calendar)
