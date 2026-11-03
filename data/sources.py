"""Market data sources behind a single interface, so yfinance can be swapped out."""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Any, Protocol

import pandas as pd

logger = logging.getLogger(__name__)

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataSourceError(RuntimeError):
    """A source could not return data for a ticker."""


class DataSource(Protocol):
    """Interface every market data source implements."""

    name: str

    def fetch_daily(self, ticker: str, start: date, end: date | None = None) -> pd.DataFrame:
        """Fetch daily bars for ``ticker`` in ``[start, end]`` (inclusive).

        Returns:
            A DataFrame with columns ``OHLCV_COLUMNS`` and a naive, normalised
            ``DatetimeIndex`` of the exchange-local session date, sorted ascending.

        Raises:
            DataSourceError: If no data could be fetched.
        """
        ...


def normalize_bars(raw: pd.DataFrame) -> pd.DataFrame:
    """Convert a raw OHLCV frame to the standard source output format."""
    df = raw.rename(columns=str.lower)
    for col in OHLCV_COLUMNS:
        if col not in df.columns:
            df[col] = float("nan")
    df = df[OHLCV_COLUMNS].astype(float)
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)  # keep the exchange-local wall date
    df.index = idx.normalize()
    df.index.name = "session_date"
    df = df.dropna(subset=["close"])
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


class YFinanceSource:
    """Daily bars from Yahoo Finance via the ``yfinance`` package."""

    name = "yfinance"

    def __init__(self, max_retries: int = 3, backoff_seconds: float = 2.0) -> None:
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def fetch_daily(self, ticker: str, start: date, end: date | None = None) -> pd.DataFrame:
        """Fetch daily bars, retrying with exponential backoff."""
        import yfinance as yf  # imported lazily so tests don't need network access

        end_excl = (end or date.today()) + timedelta(days=1)  # yfinance's end is exclusive
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw = yf.Ticker(ticker).history(
                    start=start.isoformat(),
                    end=end_excl.isoformat(),
                    interval="1d",
                    auto_adjust=False,
                    actions=False,
                    raise_errors=True,
                )
                if raw is None or raw.empty:
                    raise DataSourceError(f"yfinance returned no rows for {ticker}")
                return normalize_bars(raw)
            except Exception as exc:  # yfinance raises many exception types
                last_error = exc
                logger.warning("yfinance %s attempt %d/%d failed: %s",
                               ticker, attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * 2 ** (attempt - 1))
        raise DataSourceError(f"yfinance failed for {ticker}: {last_error}") from last_error


def get_source(cfg: dict[str, Any]) -> DataSource:
    """Build the data source named in ``cfg['data']['source']``."""
    name = cfg["data"]["source"]
    if name == "yfinance":
        return YFinanceSource(
            max_retries=int(cfg["data"].get("max_retries", 3)),
            backoff_seconds=float(cfg["data"].get("retry_backoff_seconds", 2.0)),
        )
    raise ValueError(f"unknown data source: {name}")
