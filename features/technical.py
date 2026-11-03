"""Per-bar technical features. Every function is causal: row i uses only bars <= i.

Outputs keep the input's ``available_at`` column, so the builder can attach each row
to a prediction only once that bar was available.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def slug(ticker: str) -> str:
    """Column-name prefix for a ticker, e.g. ``^NSEI`` -> ``nsei``, ``DX-Y.NYB`` -> ``dx_y_nyb``."""
    return "_".join("".join(c.lower() if c.isalnum() else " " for c in ticker).split())


def _log_ret(close: pd.Series, n: int) -> pd.Series:
    return np.log(close / close.shift(n))


def _streak(returns: pd.Series) -> pd.Series:
    """Signed length of the current run of up (+) or down (-) closes."""
    sign = np.sign(returns.fillna(0.0))
    groups = (sign != sign.shift()).cumsum()
    return sign * sign.groupby(groups).cumcount().add(1)


def index_features(bars: pd.DataFrame) -> pd.DataFrame:
    """Technical features for the index being predicted.

    Args:
        bars: Daily OHLCV with ``available_at`` (from the data store).

    Returns:
        Feature frame on the same index, plus ``close`` (used for the previous close,
        not as a feature) and ``available_at``.
    """
    o, h, l, c = (bars[k].astype(float) for k in ("open", "high", "low", "close"))
    lr = _log_ret(c, 1)
    out = pd.DataFrame(index=bars.index)
    for n in (1, 2, 5, 10, 20):
        out[f"ret_{n}"] = _log_ret(c, n)
    out["gap"] = np.log(o / c.shift(1))
    out["intraday_ret"] = np.log(c / o)
    out["range"] = np.log(h / l)
    out["close_pos"] = (c - l) / (h - l).replace(0.0, np.nan)
    out["vol_5"] = lr.rolling(5).std()
    out["vol_20"] = lr.rolling(20).std()
    out["parkinson_20"] = np.sqrt((np.log(h / l) ** 2).rolling(20).mean() / (4 * np.log(2)))
    prev_c = c.shift(1)
    true_range = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    out["atr_14"] = true_range.ewm(alpha=1 / 14, adjust=False).mean() / c
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    out["rsi_14"] = 100 - 100 / (1 + gain / loss.replace(0.0, np.nan))
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    out["ema20_50"] = ema20 / ema50 - 1
    out["close_ema20"] = c / ema20 - 1
    out["dist_high_252"] = c / h.rolling(252, min_periods=60).max() - 1
    out["dist_low_252"] = c / l.rolling(252, min_periods=60).min() - 1
    out["ret1_z"] = lr / out["vol_20"]
    out["streak"] = _streak(lr)
    out["close"] = c
    out["available_at"] = bars["available_at"]
    return out


def instrument_features(bars: pd.DataFrame, transform: str = "logret") -> pd.DataFrame:
    """Return-style features for an external cue (US index, crude, FX, ...).

    Args:
        bars: Daily OHLCV with ``available_at``.
        transform: ``"logret"`` for log returns, ``"diff"`` for level changes (yields).
    """
    c = bars["close"].astype(float)
    if transform == "diff":
        change = c.diff
    elif transform == "logret":
        def change(n: int = 1) -> pd.Series:
            return _log_ret(c, n)
    else:
        raise ValueError(f"unknown transform {transform!r}")
    out = pd.DataFrame(index=bars.index)
    out["ret_1"] = change(1)
    out["ret_5"] = change(5)
    out["ret_20"] = change(20)
    out["ret1_z"] = out["ret_1"] / out["ret_1"].rolling(20).std()
    out["available_at"] = bars["available_at"]
    return out


def vix_features(bars: pd.DataFrame, percentile_window: int = 252) -> pd.DataFrame:
    """India VIX level, changes, rolling percentile and implied 1-day move."""
    v = bars["close"].astype(float)
    out = pd.DataFrame(index=bars.index)
    out["level"] = v
    out["chg_1"] = _log_ret(v, 1)
    out["chg_5"] = _log_ret(v, 5)
    out["pct_rank"] = v.rolling(percentile_window, min_periods=60).rank(pct=True)
    out["implied_move"] = v / 100 / np.sqrt(252)
    out["available_at"] = bars["available_at"]
    return out
