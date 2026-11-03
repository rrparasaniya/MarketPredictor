"""Shared test fixtures. Tests never touch the network."""

from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import pytest

from data.calendar import TradingCalendar
from data.sources import OHLCV_COLUMNS
from settings import load_config


@pytest.fixture(scope="session")
def cfg() -> dict[str, Any]:
    return load_config()


@pytest.fixture(scope="session")
def calendar(cfg) -> TradingCalendar:
    return TradingCalendar.from_config(cfg)


def make_bars(dates: list[date] | pd.DatetimeIndex, start_price: float = 100.0, seed: int = 0) -> pd.DataFrame:
    """Synthetic, internally consistent OHLCV bars in the source output format."""
    idx = pd.DatetimeIndex(pd.to_datetime(list(dates))).normalize()
    rng = np.random.default_rng(seed)
    close = start_price * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx))))
    open_ = close * (1 + rng.normal(0, 0.003, len(idx)))
    high = np.maximum(open_, close) * 1.004
    low = np.minimum(open_, close) * 0.996
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                       "volume": 1000.0}, index=idx)[OHLCV_COLUMNS]
    df.index.name = "session_date"
    return df


class FakeSource:
    """In-memory DataSource that records calls and can be told to fail."""

    name = "fake"

    def __init__(self, data: dict[str, pd.DataFrame]) -> None:
        self.data = data
        self.calls: list[tuple[str, date, date | None]] = []
        self.fail = False

    def fetch_daily(self, ticker: str, start: date, end: date | None = None) -> pd.DataFrame:
        self.calls.append((ticker, start, end))
        if self.fail:
            raise RuntimeError("simulated outage")
        df = self.data[ticker]
        mask = df.index >= pd.Timestamp(start)
        if end is not None:
            mask &= df.index <= pd.Timestamp(end)
        return df[mask].copy()
