"""Assemble the feature matrix for one index and one scheduled run.

How look-ahead is prevented:
  1. Each source's features are computed causally on its own bars (row i uses bars <= i).
  2. Each target session D gets a cutoff time T in IST:
       morning run: D at ``morning_run_time``
       evening run: the previous session at ``evening_run_time``
  3. For every source, the row attached to D is the last bar with ``available_at < T``
     (``merge_asof``, strict). The target session's own bar is never visible.
  4. A runtime check raises ``LeakageError`` if any attached bar was available at or
     after its cutoff.
No statistics are fitted here; scaling belongs inside each training fold.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from data.calendar import TradingCalendar
from data.optional_inputs import load_all_optional_inputs
from data.store import MarketDataStore, empty_frame
from features.events import event_features
from features.targets import build_targets
from features.technical import index_features, instrument_features, slug, vix_features
from settings import parse_time

logger = logging.getLogger(__name__)

RUNS = ("morning", "evening")


class LeakageError(RuntimeError):
    """A feature used data that was not available at the prediction cutoff."""


@dataclass
class FeatureSet:
    """Features, targets and metadata, all indexed by target session date (IST).

    ``meta`` holds the cutoff, previous close/session, and for each source the session
    and ``available_at`` of the bar that was used (for logging and audits).
    """

    features: pd.DataFrame
    targets: pd.DataFrame
    meta: pd.DataFrame


def _drop_non_sessions(bars: pd.DataFrame, calendar: TradingCalendar) -> pd.DataFrame:
    """Drop Indian bars on Muhurat-only days (symbolic sessions, not regular trading)."""
    if bars.empty:
        return bars
    drop = [ts for ts in bars.index
            if calendar.is_muhurat(ts.date()) and not calendar.is_trading_day(ts.date())]
    if drop:
        logger.info("dropping %d Muhurat-only bar(s)", len(drop))
    return bars.drop(index=drop)


def nominal_cutoffs(target_dates: pd.DatetimeIndex, index_bars: pd.DataFrame,
                    run: str, cfg: dict[str, Any]) -> pd.Series:
    """Prediction time for each target session under the scheduled run.

    Morning: the target date at ``morning_run_time``. Evening: the previous index
    session (the last bar before the target date) at ``evening_run_time``.
    """
    if run == "morning":
        t = parse_time(cfg["market"]["morning_run_time"])
        cut = target_dates + pd.Timedelta(hours=t.hour, minutes=t.minute)
        return pd.Series(cut, index=target_dates)
    if run == "evening":
        t = parse_time(cfg["market"]["evening_run_time"])
        bar_dates = index_bars.index
        pos = bar_dates.searchsorted(target_dates, side="left") - 1
        prev = pd.DatetimeIndex([bar_dates[p] if p >= 0 else pd.NaT for p in pos]).tz_convert(
            cfg["timezone"]) if len(bar_dates) else pd.DatetimeIndex([pd.NaT] * len(target_dates))
        return pd.Series(prev + pd.Timedelta(hours=t.hour, minutes=t.minute), index=target_dates)
    raise ValueError(f"run must be one of {RUNS}, got {run!r}")


def _as_of_merge(cutoffs: pd.Series, feats: pd.DataFrame, prefix: str,
                 max_stale_days: float) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Attach the last row with ``available_at < cutoff`` to each cutoff.

    Returns:
        (prefixed feature values, used session dates, used available_at).
    """
    feat_cols = [c for c in feats.columns if c != "available_at"]
    right = feats.rename_axis("_session").reset_index().rename(columns={"available_at": "_avail"})
    right = right.dropna(subset=["_avail"]).sort_values("_avail")
    key_dtype = f"datetime64[ns, {cutoffs.dt.tz}]"  # merge keys must share a resolution
    right["_avail"] = right["_avail"].astype(key_dtype)
    left = pd.DataFrame({"_cutoff": cutoffs.astype(key_dtype).to_numpy()})
    merged = pd.merge_asof(left, right, left_on="_cutoff", right_on="_avail",
                           direction="backward", allow_exact_matches=False)
    age_days = (merged["_cutoff"] - merged["_avail"]) / pd.Timedelta(days=1)
    values = merged[feat_cols].astype(float)
    stale = (age_days > max_stale_days).to_numpy()[:, None]
    values = values.where(~np.broadcast_to(stale, values.shape))
    values.columns = [f"{prefix}{c}" for c in feat_cols]
    values.index = cutoffs.index
    session = merged["_session"].astype(key_dtype).set_axis(cutoffs.index)
    avail = merged["_avail"].astype(key_dtype).set_axis(cutoffs.index)
    return values, session, avail


def build_features(
    bars: dict[str, pd.DataFrame],
    cfg: dict[str, Any],
    calendar: TradingCalendar,
    index_name: str,
    run: str,
    target_dates: pd.DatetimeIndex | list | None = None,
    cutoffs: pd.Series | None = None,
    optional: dict[str, pd.DataFrame] | None = None,
) -> FeatureSet:
    """Build features and targets for ``index_name`` under the ``run`` schedule.

    Args:
        bars: Ticker -> frame from :class:`MarketDataStore` (with ``available_at``).
        cfg: Project config.
        calendar: NSE trading calendar.
        index_name: Key under ``cfg['indices']`` (e.g. ``"nifty"``).
        run: ``"morning"`` or ``"evening"``.
        target_dates: Sessions to build rows for. Defaults to every index session
            after the first.
        cutoffs: Explicit prediction times per target (e.g. the live "now").
            Defaults to :func:`nominal_cutoffs`.
        optional: Optional input frames by name (see ``data.optional_inputs``).

    Returns:
        A :class:`FeatureSet`.

    Raises:
        LeakageError: If any attached bar was not available before its cutoff.
    """
    if run not in RUNS:
        raise ValueError(f"run must be one of {RUNS}, got {run!r}")
    tz = cfg["timezone"]
    fcfg = cfg["features"]
    run_cfg = fcfg["runs"][run]
    max_stale = float(fcfg["max_staleness_days"])
    idx_ticker = cfg["indices"][index_name]["ticker"]

    def get_bars(ticker: str) -> pd.DataFrame:
        df = bars.get(ticker)
        if df is None or df.empty:
            logger.warning("%s: no bars; its features will be missing", ticker)
            return empty_frame(tz)
        if cfg["instruments"][ticker]["timezone"] == tz:
            df = _drop_non_sessions(df, calendar)
        return df

    idx_bars = get_bars(idx_ticker)
    if target_dates is None:
        target_dates = idx_bars.index[1:]
    target_dates = pd.DatetimeIndex(target_dates)
    if target_dates.tz is None:
        target_dates = target_dates.tz_localize(tz)
    target_dates = target_dates.tz_convert(tz).normalize().sort_values().unique()
    target_dates.name = "session_date"

    if cutoffs is None:
        cutoffs = nominal_cutoffs(target_dates, idx_bars, run, cfg)
    else:
        cutoffs = pd.Series(pd.DatetimeIndex(cutoffs.reindex(target_dates)), index=target_dates)
        if cutoffs.dt.tz is None:
            raise ValueError("cutoffs must be timezone-aware")
    cutoffs = cutoffs.dropna()
    target_dates = cutoffs.index
    if not cutoffs.is_monotonic_increasing:
        raise ValueError("cutoffs must increase with target date")

    meta = pd.DataFrame({"cutoff": cutoffs}, index=target_dates)
    parts: list[pd.DataFrame] = []

    def attach(feats: pd.DataFrame, prefix: str, ticker: str | None = None) -> pd.DataFrame:
        values, session, avail = _as_of_merge(cutoffs, feats, prefix, max_stale)
        meta[f"{prefix}session"] = session
        meta[f"{prefix}available_at"] = avail
        if ticker in fcfg.get("age_features", []):
            values[f"{prefix}age_h"] = (cutoffs - avail) / pd.Timedelta(hours=1)
        parts.append(values)
        return values

    # 1. The target index's own technicals.
    idx_vals = attach(index_features(idx_bars), "idx_", idx_ticker)
    meta["prev_close"] = idx_vals.pop("idx_close")
    meta["prev_session"] = meta.pop("idx_session")

    # 2. Other instruments allowed in this run.
    for ticker, inst in cfg["instruments"].items():
        if ticker == idx_ticker or inst["group"] not in run_cfg["groups"]:
            continue
        b = get_bars(ticker)
        if inst["group"] == "vix":
            feats = vix_features(b, int(fcfg.get("vix_percentile_window", 252)))
        else:
            feats = instrument_features(b, fcfg.get("transforms", {}).get(ticker, "logret"))
        attach(feats, f"{slug(ticker)}_", ticker)

    # 3. Optional CSV inputs allowed in this run (skipped if the file isn't there).
    optional = optional or {}
    for name in run_cfg.get("optional_inputs", []):
        df = optional.get(name)
        if df is None or df.empty:
            continue
        spec = cfg["optional_inputs"][name]
        numeric = df.drop(columns="available_at").select_dtypes("number")
        vals = attach(pd.concat([numeric, df[["available_at"]]], axis=1), f"opt_{name}_")
        for col in spec.get("relative_to_prev_close", []):
            key = f"opt_{name}_{col}"
            if key in vals:
                parts[-1][key] = np.log(vals[key] / meta["prev_close"])

    # 4. Runtime look-ahead guard.
    for col in [c for c in meta.columns if c.endswith("available_at")]:
        bad = meta[col].notna() & ~(meta[col] < meta["cutoff"])
        if bad.any():
            raise LeakageError(f"{col}: {int(bad.sum())} rows use data available after the cutoff")

    # 5. Calendar/event features for the target date (known in advance).
    idx_dates = [ts.date() for ts in idx_bars.index]
    parts.append(event_features(target_dates, cfg, calendar, index_name, idx_dates))

    features = pd.concat(parts, axis=1)
    features.index.name = "session_date"
    targets = build_targets(idx_bars, meta["prev_close"], cfg)
    return FeatureSet(features=features, targets=targets, meta=meta)


def required_tickers(cfg: dict[str, Any], index_name: str, run: str) -> list[str]:
    """Tickers a given index/run needs."""
    groups = cfg["features"]["runs"][run]["groups"]
    idx = cfg["indices"][index_name]["ticker"]
    return [idx] + [t for t, i in cfg["instruments"].items() if t != idx and i["group"] in groups]


def build_dataset(store: MarketDataStore, cfg: dict[str, Any], calendar: TradingCalendar,
                  index_name: str, run: str, **kwargs: Any) -> FeatureSet:
    """Convenience wrapper: load cached bars and optional inputs, then build features."""
    bars = store.get_many(required_tickers(cfg, index_name, run))
    return build_features(bars, cfg, calendar, index_name, run,
                          optional=load_all_optional_inputs(cfg), **kwargs)
