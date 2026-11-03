"""Prediction targets for the next session: direction, gap class, and range."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

GAP_DOWN, GAP_FLAT, GAP_UP = -1, 0, 1


def build_targets(index_bars: pd.DataFrame, prev_close: pd.Series, cfg: dict[str, Any]) -> pd.DataFrame:
    """Targets for each session in ``prev_close.index``.

    Args:
        index_bars: The index's daily bars (session-date index, tz IST).
        prev_close: Previous session close for each target date (from the as-of merge).
        cfg: Project config (``prediction`` thresholds).

    Returns:
        Columns ``y_direction`` (1/0), ``y_gap`` (-1/0/1), and log ratios to the previous
        close: ``y_open``, ``y_high``, ``y_low``, ``y_close``. NaN where the target
        session has no bar yet (live predictions).
    """
    thr = float(cfg["prediction"]["direction_threshold"])
    gap_thr = float(cfg["prediction"]["gap_threshold"])
    bars = index_bars.reindex(prev_close.index)
    pc = prev_close.astype(float)
    out = pd.DataFrame(index=prev_close.index)
    for col in ("open", "high", "low", "close"):
        out[f"y_{col}"] = np.log(bars[col].astype(float) / pc)
    has = bars["close"].notna() & pc.notna()
    out["y_direction"] = np.where(has, (bars["close"] > pc * (1 + thr)).astype(float), np.nan)
    gap = bars["open"] / pc - 1
    out["y_gap"] = np.select([gap > gap_thr, gap < -gap_thr], [GAP_UP, GAP_DOWN], GAP_FLAT).astype(float)
    out.loc[~(bars["open"].notna() & pc.notna()), "y_gap"] = np.nan
    return out
