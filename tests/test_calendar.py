"""NSE trading calendar tests."""

from datetime import date

import pytest


def test_weekends_are_not_trading_days(calendar):
    assert not calendar.is_trading_day(date(2026, 11, 7))   # Saturday
    assert not calendar.is_trading_day(date(2026, 11, 8))   # Sunday (Muhurat only)


def test_listed_holidays_are_not_trading_days(calendar):
    assert not calendar.is_trading_day(date(2026, 11, 10))  # Diwali Balipratipada
    assert not calendar.is_trading_day(date(2026, 1, 26))   # Republic Day
    assert calendar.is_trading_day(date(2026, 11, 3))       # ordinary Tuesday


def test_special_weekend_session_is_trading_day(calendar):
    assert calendar.is_trading_day(date(2025, 2, 1))        # Budget Saturday


def test_muhurat_is_not_a_regular_session(calendar):
    assert calendar.is_muhurat(date(2026, 11, 8))
    assert calendar.is_muhurat(date(2025, 10, 21))
    assert not calendar.is_trading_day(date(2025, 10, 21))  # Laxmi Pujan holiday


def test_next_trading_day_skips_weekend_and_holiday(calendar):
    assert calendar.next_trading_day(date(2026, 11, 6)) == date(2026, 11, 9)    # Fri -> Mon
    assert calendar.next_trading_day(date(2026, 11, 9)) == date(2026, 11, 11)   # skips Tue holiday
    assert calendar.next_trading_day(date(2026, 4, 2)) == date(2026, 4, 6)      # Good Friday + weekend


def test_previous_trading_day(calendar):
    assert calendar.previous_trading_day(date(2026, 11, 11)) == date(2026, 11, 9)
    assert calendar.previous_trading_day(date(2026, 11, 9)) == date(2026, 11, 6)


def test_trading_days_range(calendar):
    days = calendar.trading_days(date(2026, 11, 2), date(2026, 11, 13))
    assert date(2026, 11, 10) not in days
    assert len(days) == 9


def test_uncovered_year_falls_back_to_weekdays_with_warning(calendar, caplog):
    assert not calendar.is_covered(date(2030, 1, 1))
    with caplog.at_level("WARNING"):
        assert calendar.is_trading_day(date(2030, 1, 2))  # Wednesday
    assert "no entries for 2030" in caplog.text


def test_holiday_file_has_no_weekend_holidays(calendar):
    # A "holiday" on a weekend is usually a data-entry mistake.
    assert all(d.weekday() < 5 for d in calendar.holidays)


@pytest.mark.parametrize("year", [2024, 2025, 2026])
def test_years_covered(calendar, year):
    assert year in calendar.covered_years
