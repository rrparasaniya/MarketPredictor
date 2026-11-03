"""Cached market data with IST availability timestamps.

Every stored daily bar has two time fields:

* ``session_date`` (index): the exchange-local trading date, at 00:00 IST.
* ``available_at``: the earliest IST time the bar is final and usable as a feature
  (the exchange close plus ``publish_delay_minutes``).

Feature code must filter with :func:`available_as_of` so a prediction made at time T
only sees bars with ``available_at < T``. This is the main guard against look-ahead bias.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from data.sources import OHLCV_COLUMNS, DataSource, get_source
from settings import ist, parse_time, resolve_path

logger = logging.getLogger(__name__)

FRAME_COLUMNS = OHLCV_COLUMNS + ["available_at"]


def empty_frame(tz: str) -> pd.DataFrame:
    """An empty frame in the store's output format."""
    df = pd.DataFrame(columns=FRAME_COLUMNS)
    df.index = pd.DatetimeIndex([], tz=tz, name="session_date")
    df["available_at"] = pd.to_datetime(df["available_at"]).dt.tz_localize(tz)
    return df


def compute_available_at(
    session_dates: pd.DatetimeIndex,
    exchange_tz: str,
    close_time: str,
    target_tz: str,
    delay_minutes: float,
) -> pd.DatetimeIndex:
    """IST time each bar becomes final: local close, converted to IST, plus a delay.

    Args:
        session_dates: Naive exchange-local session dates.
        exchange_tz: The exchange's IANA timezone (handles DST, e.g. US 1:30 vs 2:30 IST).
        close_time: Local close time ("HH:MM").
        target_tz: Output timezone (Asia/Kolkata).
        delay_minutes: Extra publish delay.
    """
    t = parse_time(close_time)
    offset = pd.Timedelta(hours=t.hour, minutes=t.minute)
    local_close = (pd.DatetimeIndex(session_dates).normalize() + offset).tz_localize(exchange_tz)
    return local_close.tz_convert(target_tz) + pd.Timedelta(minutes=delay_minutes)


def available_as_of(df: pd.DataFrame, cutoff: datetime | pd.Timestamp) -> pd.DataFrame:
    """Rows of ``df`` that were available strictly before ``cutoff``.

    Raises:
        ValueError: If ``cutoff`` is naive.
    """
    cutoff_ts = pd.Timestamp(cutoff)
    if cutoff_ts.tzinfo is None:
        raise ValueError("cutoff must be timezone-aware")
    return df[df["available_at"] < cutoff_ts]


def validate_bars(df: pd.DataFrame, ticker: str, max_gap_days: int = 10) -> list[str]:
    """Return (and log) data quality problems. Does not modify the data."""
    issues: list[str] = []
    if df.empty:
        return issues
    prices = df[["open", "high", "low", "close"]]
    if (prices <= 0).any().any():
        issues.append(f"{int((prices <= 0).any(axis=1).sum())} rows with non-positive prices")
    tol = 1e-6
    hi_bad = df["high"] + tol < df[["open", "close"]].max(axis=1)
    lo_bad = df["low"] - tol > df[["open", "close"]].min(axis=1)
    if hi_bad.any():
        issues.append(f"{int(hi_bad.sum())} rows with high below open/close")
    if lo_bad.any():
        issues.append(f"{int(lo_bad.sum())} rows with low above open/close")
    if df.index.has_duplicates:
        issues.append("duplicate session dates")
    gaps = pd.Series(df.index).diff().dt.days
    big = gaps[gaps > max_gap_days]
    if not big.empty:
        issues.append(f"{len(big)} gaps longer than {max_gap_days} calendar days")
    for msg in issues:
        logger.warning("%s: %s", ticker, msg)
    return issues


@dataclass
class UpdateResult:
    """Outcome of updating one ticker."""

    ticker: str
    ok: bool
    rows: int
    last_session: date | None
    last_available_at: pd.Timestamp | None
    message: str = ""


class MarketDataStore:
    """Downloads, caches, and serves daily bars with availability timestamps."""

    def __init__(
        self,
        cfg: dict[str, Any],
        source: DataSource | None = None,
        cache_dir: str | Path | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        """
        Args:
            cfg: Project config.
            source: Data source. Defaults to the one named in config.
            cache_dir: Cache directory. Defaults to ``cfg['data']['cache_dir']``.
            now_fn: Returns the current tz-aware time (injectable for tests).
        """
        self.cfg = cfg
        self.tz = cfg["timezone"]
        self.source = source if source is not None else get_source(cfg)
        self.cache_dir = resolve_path(cache_dir or cfg["data"]["cache_dir"])
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.now_fn = now_fn or (lambda: datetime.now(ist(cfg)))

    # ------------------------------------------------------------------ paths
    def _stem(self, ticker: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in ticker).strip("_")

    def _csv_path(self, ticker: str) -> Path:
        return self.cache_dir / f"{self._stem(ticker)}.csv"

    def _meta_path(self, ticker: str) -> Path:
        return self.cache_dir / f"{self._stem(ticker)}.meta.json"

    # ------------------------------------------------------------------ cache io
    def _read_cache(self, ticker: str) -> pd.DataFrame:
        """Raw cached bars (naive session-date index) or an empty frame."""
        path = self._csv_path(ticker)
        if not path.exists():
            return pd.DataFrame(columns=OHLCV_COLUMNS, index=pd.DatetimeIndex([], name="session_date"))
        df = pd.read_csv(path, index_col="session_date", parse_dates=["session_date"])
        return df[OHLCV_COLUMNS].astype(float)

    def _write_cache(self, ticker: str, raw: pd.DataFrame, fetched_at: datetime) -> None:
        tmp = self._csv_path(ticker).with_suffix(".csv.tmp")
        raw.to_csv(tmp, index_label="session_date", date_format="%Y-%m-%d")
        tmp.replace(self._csv_path(ticker))
        meta = {"ticker": ticker, "source": self.source.name,
                "fetched_at": fetched_at.isoformat(), "rows": len(raw)}
        self._meta_path(ticker).write_text(json.dumps(meta, indent=2))

    def last_fetched_at(self, ticker: str) -> datetime | None:
        """When ``ticker`` was last downloaded, or None."""
        path = self._meta_path(ticker)
        if not path.exists():
            return None
        return datetime.fromisoformat(json.loads(path.read_text())["fetched_at"])

    # ------------------------------------------------------------------ public api
    def _instrument(self, ticker: str) -> dict[str, Any]:
        try:
            return self.cfg["instruments"][ticker]
        except KeyError as exc:
            raise KeyError(f"{ticker} is not configured under 'instruments' in config.yaml") from exc

    def _with_availability(self, ticker: str, raw: pd.DataFrame) -> pd.DataFrame:
        """Add ``available_at`` and convert the index to tz-aware IST dates."""
        if raw.empty:
            return empty_frame(self.tz)
        inst = self._instrument(ticker)
        avail = compute_available_at(
            pd.DatetimeIndex(raw.index), inst["timezone"], inst["close_time"], self.tz,
            float(self.cfg["data"].get("publish_delay_minutes", 0)),
        )
        out = raw[OHLCV_COLUMNS].copy()
        out["available_at"] = avail
        out.index = pd.DatetimeIndex(raw.index).tz_localize(self.tz)
        out.index.name = "session_date"
        return out

    def _drop_unfinished(self, ticker: str, raw: pd.DataFrame, now: datetime) -> pd.DataFrame:
        """Remove bars that aren't final yet (e.g. today's in-progress session)."""
        if raw.empty:
            return raw
        framed = self._with_availability(ticker, raw)
        keep = np.asarray(framed["available_at"] <= pd.Timestamp(now))
        dropped = int((~keep).sum())
        if dropped:
            logger.info("%s: dropped %d unfinished bar(s)", ticker, dropped)
        return raw[keep]

    def update(self, ticker: str, full: bool = False) -> UpdateResult:
        """Download new bars for ``ticker`` and merge them into the cache.

        Downloads only the last ``refetch_overlap_days`` (or full history if the cache
        is empty or ``full=True``). On failure the existing cache is kept.
        """
        self._instrument(ticker)
        now = self.now_fn()
        cached = self._read_cache(ticker)
        if full or cached.empty:
            start = date.fromisoformat(str(self.cfg["data"]["history_start"]))
        else:
            overlap = int(self.cfg["data"].get("refetch_overlap_days", 7))
            start = cached.index.max().date() - timedelta(days=overlap)
        try:
            fetched = self.source.fetch_daily(ticker, start, now.astimezone(ist(self.cfg)).date())
        except Exception as exc:
            msg = f"fetch failed, keeping {len(cached)} cached rows: {exc}"
            logger.error("%s: %s", ticker, msg)
            return self._result(ticker, cached, ok=False, message=msg)

        fetched = self._drop_unfinished(ticker, fetched, now)
        merged = pd.concat([cached[cached.index < fetched.index.min()] if not fetched.empty else cached,
                            fetched])
        merged = merged[~merged.index.duplicated(keep="last")].sort_index()
        validate_bars(merged, ticker, int(self.cfg["data"].get("max_gap_calendar_days", 10)))
        self._write_cache(ticker, merged, now)
        return self._result(ticker, merged, ok=True, message=f"fetched {len(fetched)} rows")

    def _result(self, ticker: str, raw: pd.DataFrame, ok: bool, message: str) -> UpdateResult:
        framed = self._with_availability(ticker, raw)
        last = framed.index.max().date() if not framed.empty else None
        last_avail = framed["available_at"].max() if not framed.empty else None
        return UpdateResult(ticker, ok, len(framed), last, last_avail, message)

    def update_all(self, full: bool = False) -> list[UpdateResult]:
        """Update every configured instrument. One failure does not stop the others."""
        return [self.update(t, full=full) for t in self.cfg["instruments"]]

    def get(self, ticker: str) -> pd.DataFrame:
        """Cached bars for ``ticker`` with ``available_at``; downloads if not cached.

        Returns an empty frame (and logs an error) if nothing could be loaded.
        """
        raw = self._read_cache(ticker)
        if raw.empty:
            self.update(ticker)
            raw = self._read_cache(ticker)
        if raw.empty:
            logger.error("%s: no data available", ticker)
        return self._with_availability(ticker, raw)

    def get_many(self, tickers: list[str] | None = None) -> dict[str, pd.DataFrame]:
        """``get`` for several tickers (all configured instruments by default)."""
        return {t: self.get(t) for t in (tickers or list(self.cfg["instruments"]))}
