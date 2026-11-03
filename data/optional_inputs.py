"""Optional CSV inputs (FII/DII flows, GIFT Nifty, PCR/OI): loaded only if present."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from settings import parse_time, resolve_path

logger = logging.getLogger(__name__)


def load_optional_input(name: str, cfg: dict[str, Any]) -> pd.DataFrame | None:
    """Load the optional CSV ``name`` from ``cfg['optional_inputs']``.

    The result is indexed by session date (00:00 IST) and has an ``available_at``
    column (tz-aware IST), so the same no-look-ahead filter applies to it.

    Returns:
        The data, or None if the input isn't configured, the file is missing, or
        it can't be parsed. Missing optional data never stops the pipeline.
    """
    spec = cfg.get("optional_inputs", {}).get(name)
    if spec is None:
        logger.info("optional input %s not configured; skipping", name)
        return None
    path = resolve_path(spec["path"])
    if not path.exists():
        logger.info("optional input %s not found at %s; skipping", name, path)
        return None
    tz = cfg["timezone"]
    try:
        df = pd.read_csv(path)
        date_col = spec.get("date_column", "date")
        dates = pd.DatetimeIndex(pd.to_datetime(df.pop(date_col))).normalize()
        if dates.tz is None:
            dates = dates.tz_localize(tz)
        else:
            dates = dates.tz_convert(tz).normalize()
        if "available_at" in df.columns:
            avail = pd.to_datetime(df.pop("available_at"), utc=False)
            if getattr(avail.dt, "tz", None) is None:
                raise ValueError("available_at must include a timezone offset")
            avail = avail.dt.tz_convert(tz)
        else:
            t = parse_time(spec["available_time"])
            avail = pd.Series(dates + pd.Timedelta(hours=t.hour, minutes=t.minute))
        df.index = dates
        df.index.name = "session_date"
        df["available_at"] = pd.DatetimeIndex(avail)
        df = df[~df.index.duplicated(keep="last")].sort_index()
    except Exception as exc:
        logger.warning("optional input %s at %s could not be parsed (%s); skipping", name, path, exc)
        return None
    logger.info("loaded optional input %s: %d rows", name, len(df))
    return df


def load_all_optional_inputs(cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Load every configured optional input that is present."""
    out = {}
    for name in cfg.get("optional_inputs", {}):
        df = load_optional_input(name, cfg)
        if df is not None:
            out[name] = df
    return out
