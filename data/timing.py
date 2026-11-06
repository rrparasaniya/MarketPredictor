"""Decide which trading session to predict, given the current time in IST."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from data.calendar import TradingCalendar
from settings import ist, parse_time


class PredictionMode(str, Enum):
    """Where ``now`` falls relative to the trading day."""

    PRE_OPEN = "pre_open"              # before 09:15 on a trading day: predict today
    INTRADAY = "intraday"              # 09:15-15:30: show today's existing prediction
    POST_CLOSE = "post_close"          # after 15:30: predict the next session
    NON_TRADING_DAY = "non_trading_day"  # weekend/holiday: predict the next session


@dataclass(frozen=True)
class PredictionTarget:
    """The session to predict and the data cutoff for it.

    Attributes:
        target_date: The trading session being predicted.
        mode: Where ``as_of`` falls relative to market hours.
        label: "today", "tomorrow" or "next session", for the dashboard.
        generate_new: False during market hours (show the existing prediction).
        as_of: The data cutoff (tz-aware IST). Only data available before it is used.
    """

    target_date: date
    mode: PredictionMode
    label: str
    generate_new: bool
    as_of: datetime


def resolve_prediction_target(
    now: datetime, calendar: TradingCalendar, cfg: dict[str, Any]
) -> PredictionTarget:
    """Work out which session to predict at time ``now``.

    Args:
        now: Current time. Must be timezone-aware; it is converted to IST.
        calendar: NSE trading calendar.
        cfg: Project config (market hours and timezone).

    Returns:
        The prediction target.

    Raises:
        ValueError: If ``now`` is naive.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    now_ist = now.astimezone(ist(cfg))
    today = now_ist.date()
    open_t = parse_time(cfg["market"]["open_time"])
    close_t = parse_time(cfg["market"]["close_time"])

    if not calendar.is_trading_day(today):
        target, mode, new = calendar.next_trading_day(today), PredictionMode.NON_TRADING_DAY, True
    elif now_ist.time() < open_t:
        target, mode, new = today, PredictionMode.PRE_OPEN, True
    elif now_ist.time() < close_t:
        target, mode, new = today, PredictionMode.INTRADAY, False
    else:
        target, mode, new = calendar.next_trading_day(today), PredictionMode.POST_CLOSE, True

    days_ahead = (target - today).days
    label = {0: "today", 1: "tomorrow"}.get(days_ahead, "next session")
    return PredictionTarget(target, mode, label, new, now_ist)


def run_for_target(target: PredictionTarget, cfg: dict[str, Any]) -> str:
    """Which model set ("morning" or "evening") matches the data available at ``target.as_of``.

    The morning models were trained on an 08:45 IST cutoff, when the previous US session
    and US-hours macro bars (closing up to ~03:45 IST) are known. A pre-open run before
    ``market.morning_inputs_ready_time`` doesn't have those yet, so it uses the evening
    models, whose features match that information set. Every other mode is "evening".
    """
    ready = parse_time(cfg["market"].get("morning_inputs_ready_time", "04:00"))
    if target.mode is PredictionMode.PRE_OPEN and target.as_of.time() >= ready:
        return "morning"
    return "evening"


def expected_prev_session(target_date: date, calendar: TradingCalendar) -> date:
    """The last regular weekday session before ``target_date``.

    Weekend special sessions (e.g. a Budget Sunday) are skipped because Yahoo often has no
    bar for them, so the latest bar on hand is the weekday session before.
    """
    d = calendar.previous_trading_day(target_date)
    while d.weekday() >= 5:
        d = calendar.previous_trading_day(d)
    return d


def inputs_are_current(prev_session: date, target_date: date, calendar: TradingCalendar) -> bool:
    """Whether the index's latest final bar is the session right before ``target_date``.

    False means a forecast would skip a session, e.g. a run at 15:31 before the day's bar
    is final (15:45), or a data outage. Such a forecast must not be made.
    """
    return prev_session >= expected_prev_session(target_date, calendar)
