"""NSE trading calendar built from the holiday CSV (not weekdays alone)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from settings import resolve_path

logger = logging.getLogger(__name__)

_VALID_TYPES = {"holiday", "special_session", "muhurat"}
_MAX_SEARCH_DAYS = 30


@dataclass(frozen=True)
class TradingCalendar:
    """Regular NSE trading sessions.

    A date is a regular trading day if it is a weekday that is not a listed holiday,
    or a weekend date listed as a special session. Muhurat sessions are symbolic
    and are not regular trading days.
    """

    holidays: frozenset[date]
    special_sessions: frozenset[date] = frozenset()
    muhurat_sessions: frozenset[date] = frozenset()
    covered_years: frozenset[int] = frozenset()
    _warned_years: set[int] = field(default_factory=set, compare=False, repr=False)

    @classmethod
    def from_csv(cls, path: str | Path) -> TradingCalendar:
        """Load the calendar from a CSV with ``date,type,description`` columns."""
        df = pd.read_csv(resolve_path(path), comment="#", dtype=str)
        df["type"] = df["type"].str.strip()
        bad = set(df["type"]) - _VALID_TYPES
        if bad:
            raise ValueError(f"unknown calendar types in {path}: {bad}")
        dates = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.date
        by_type = {t: frozenset(dates[df["type"] == t]) for t in _VALID_TYPES}
        return cls(
            holidays=by_type["holiday"],
            special_sessions=by_type["special_session"],
            muhurat_sessions=by_type["muhurat"],
            covered_years=frozenset(d.year for d in by_type["holiday"]),
        )

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> TradingCalendar:
        """Load the calendar from the path in ``cfg['market']['holidays_file']``."""
        return cls.from_csv(cfg["market"]["holidays_file"])

    def is_covered(self, d: date) -> bool:
        """Whether the holiday file includes ``d``'s year."""
        return d.year in self.covered_years

    def is_trading_day(self, d: date) -> bool:
        """Whether ``d`` is a regular NSE trading session."""
        if not self.is_covered(d) and d.year not in self._warned_years:
            self._warned_years.add(d.year)
            logger.warning(
                "NSE holiday calendar has no entries for %s; falling back to weekdays. "
                "Add that year's holidays to the calendar file.",
                d.year,
            )
        if d in self.special_sessions:
            return True
        if d.weekday() >= 5:
            return False
        return d not in self.holidays

    def is_muhurat(self, d: date) -> bool:
        """Whether ``d`` has a Muhurat trading session."""
        return d in self.muhurat_sessions

    def next_trading_day(self, d: date) -> date:
        """First regular trading day strictly after ``d``."""
        for i in range(1, _MAX_SEARCH_DAYS + 1):
            cand = d + timedelta(days=i)
            if self.is_trading_day(cand):
                return cand
        raise RuntimeError(f"no trading day within {_MAX_SEARCH_DAYS} days after {d}")

    def previous_trading_day(self, d: date) -> date:
        """Last regular trading day strictly before ``d``."""
        for i in range(1, _MAX_SEARCH_DAYS + 1):
            cand = d - timedelta(days=i)
            if self.is_trading_day(cand):
                return cand
        raise RuntimeError(f"no trading day within {_MAX_SEARCH_DAYS} days before {d}")

    def trading_days(self, start: date, end: date) -> list[date]:
        """All regular trading days in ``[start, end]``."""
        days = (start + timedelta(days=i) for i in range((end - start).days + 1))
        return [d for d in days if self.is_trading_day(d)]
