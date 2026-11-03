"""Calendar and event features for the target session (expiry, RBI, Budget, ...).

These depend only on the target date and schedules known in advance, never on prices.
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from data.calendar import TradingCalendar
from settings import resolve_path

WEEKDAYS = {name: i for i, name in enumerate(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])}


def session_days(index_dates: Iterable[date], calendar: TradingCalendar,
                 start: date, end: date) -> list[date]:
    """Trading sessions in ``[start, end]``.

    Uses the NSE holiday calendar for years it covers. For other years it uses the
    dates present in the index data, and after the data ends, weekdays (with a warning).
    """
    data_days = sorted(set(index_dates))
    last_data = data_days[-1] if data_days else start - timedelta(days=1)
    out: list[date] = []
    for year in range(start.year, end.year + 1):
        ys, ye = max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
        if year in calendar.covered_years:
            out += calendar.trading_days(ys, ye)
            continue
        out += [d for d in data_days if ys <= d <= min(ye, last_data)]
        if ye > last_data:
            out += calendar.trading_days(max(ys, last_data + timedelta(days=1)), ye)
    return sorted(set(out))


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    nxt = date(year + month // 12, month % 12 + 1, 1)
    d = nxt - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _roll_back(d: date, day_set: set[date], floor: date) -> date | None:
    """Move a holiday expiry back to the previous trading day."""
    while d >= floor:
        if d in day_set:
            return d
        d -= timedelta(days=1)
    return None


def expiry_dates(schedule: list[dict[str, Any]], days: list[date]) -> tuple[set[date], set[date]]:
    """All expiry dates and monthly expiry dates within the span of ``days``.

    Args:
        schedule: Dated rules from ``indices.<name>.expiry_schedule``.
        days: Sorted trading sessions.

    Returns:
        ``(all_expiries, monthly_expiries)``.
    """
    if not days:
        return set(), set()
    day_set = set(days)
    rules = sorted(schedule, key=lambda r: r["from"])
    all_exp: set[date] = set()
    monthly: set[date] = set()
    for i, rule in enumerate(rules):
        seg_start = max(date.fromisoformat(str(rule["from"])), days[0])
        seg_end = days[-1]
        if i + 1 < len(rules):
            seg_end = min(seg_end, date.fromisoformat(str(rules[i + 1]["from"])) - timedelta(days=1))
        if seg_start > seg_end:
            continue
        wd = WEEKDAYS[rule["weekday"]]
        floor = seg_start - timedelta(days=7)
        y, m = seg_start.year, seg_start.month
        while date(y, m, 1) <= seg_end:
            nominal = _last_weekday_of_month(y, m, wd)
            if seg_start <= nominal <= seg_end and (d := _roll_back(nominal, day_set, floor)):
                monthly.add(d)
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        if rule["frequency"] == "weekly":
            d = seg_start + timedelta(days=(wd - seg_start.weekday()) % 7)
            while d <= seg_end:
                if (rolled := _roll_back(d, day_set, floor)):
                    all_exp.add(rolled)
                d += timedelta(days=7)
        elif rule["frequency"] != "monthly":
            raise ValueError(f"unknown expiry frequency {rule['frequency']!r}")
    return all_exp | monthly, monthly


def load_events(cfg: dict[str, Any]) -> pd.DataFrame:
    """Load the events CSV (``date,type,description``)."""
    df = pd.read_csv(resolve_path(cfg["events"]["file"]), comment="#", dtype=str)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.date
    unknown = set(df["type"]) - set(cfg["events"]["coverage"])
    if unknown:
        raise ValueError(f"event types without coverage in config: {unknown}")
    return df


def _next_session(d: date, days: list[date]) -> date | None:
    i = bisect.bisect_left(days, d)
    return days[i] if i < len(days) else None


def _in_windows(d: date, windows: list[list[str]]) -> bool:
    md = d.strftime("%m-%d")
    return any(lo <= md <= hi for lo, hi in windows)


def event_features(target_dates: pd.DatetimeIndex, cfg: dict[str, Any], calendar: TradingCalendar,
                   index_name: str, index_dates: Iterable[date]) -> pd.DataFrame:
    """Calendar/event features for each target session.

    Args:
        target_dates: Target session dates (tz-aware IST, normalised).
        cfg: Project config.
        calendar: NSE trading calendar.
        index_name: Key under ``cfg['indices']`` (expiry schedule differs by index).
        index_dates: Session dates present in the index data.
    """
    targets = [ts.date() for ts in target_dates]
    out = pd.DataFrame(index=target_dates)
    if not targets:
        return out
    days = session_days(index_dates, calendar, min(targets) - timedelta(days=15),
                        max(targets) + timedelta(days=45))
    pos = {d: i for i, d in enumerate(days)}

    all_exp, monthly = expiry_dates(cfg["indices"][index_name]["expiry_schedule"], days)
    exp_sorted = sorted(all_exp)
    exp_pos = [pos[e] for e in exp_sorted]

    def sessions_to_expiry(d: date) -> float:
        p = pos.get(d, bisect.bisect_left(days, d))
        j = bisect.bisect_left(exp_pos, p)
        return float(exp_pos[j] - p) if j < len(exp_pos) else np.nan

    def prev_gap(d: date) -> float:
        i = bisect.bisect_left(days, d)
        return float((d - days[i - 1]).days) if i > 0 else np.nan

    def next_gap(d: date) -> float:
        i = bisect.bisect_right(days, d)
        return float((days[i] - d).days) if i < len(days) else np.nan

    out["dow"] = [float(d.weekday()) for d in targets]
    out["month"] = [float(d.month) for d in targets]
    out["is_expiry"] = [float(d in all_exp) for d in targets]
    out["is_monthly_expiry"] = [float(d in monthly) for d in targets]
    out["sessions_to_expiry"] = [sessions_to_expiry(d) for d in targets]
    out["days_since_prev_session"] = [prev_gap(d) for d in targets]
    out["days_to_next_session"] = [next_gap(d) for d in targets]
    out["is_results_season"] = [float(_in_windows(d, cfg["events"]["results_season"])) for d in targets]
    out["after_muhurat"] = [
        float(any(m < d and m >= d - timedelta(days=int(g)) for m in calendar.muhurat_sessions))
        if not np.isnan(g) else np.nan
        for d, g in zip(targets, out["days_since_prev_session"])
    ]

    events = load_events(cfg)
    for etype, (lo, hi) in cfg["events"]["coverage"].items():
        lo_d, hi_d = date.fromisoformat(str(lo)), date.fromisoformat(str(hi))
        sessions = {_next_session(d, days) for d in events.loc[events["type"] == etype, "date"]}
        out[f"is_{etype}"] = [
            float(d in sessions) if lo_d <= d <= hi_d else np.nan for d in targets
        ]
    return out
