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


SYNTH_START, SYNTH_END = "2024-01-01", "2026-11-06"


@pytest.fixture(scope="session")
def market_bars(cfg, calendar, tmp_path_factory) -> dict[str, pd.DataFrame]:
    """Synthetic bars for every configured instrument, cached through the real store.

    Indian instruments trade on NSE sessions; others on weekdays. "now" is far in the
    future, so every bar is stored; tests apply their own cutoffs.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from data.store import MarketDataStore

    nse_days = calendar.trading_days(date.fromisoformat(SYNTH_START), date.fromisoformat(SYNTH_END))
    weekdays = pd.bdate_range(SYNTH_START, SYNTH_END)
    data = {}
    for i, (ticker, inst) in enumerate(cfg["instruments"].items()):
        days = nse_days if inst["timezone"] == "Asia/Kolkata" else weekdays
        price = 15.0 if inst["group"] == "vix" else 4.0 if ticker == "^TNX" else 1000.0 * (i + 1)
        data[ticker] = make_bars(days, start_price=price, seed=i)
    c = dict(cfg, data=dict(cfg["data"], history_start=SYNTH_START))
    store = MarketDataStore(c, source=FakeSource(data), cache_dir=tmp_path_factory.mktemp("bars"),
                            now_fn=lambda: datetime(2027, 1, 1, tzinfo=ZoneInfo("Asia/Kolkata")))
    store.update_all()
    return store.get_many()
