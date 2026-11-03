"""Load and validate project configuration from ``config.yaml``."""

from __future__ import annotations

import logging
from datetime import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

_REQUIRED_SECTIONS = ("timezone", "market", "indices", "data", "instruments")


class ConfigError(ValueError):
    """Raised when config.yaml is missing required settings."""


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Read and validate the YAML config.

    Args:
        path: Config file path. Defaults to ``config.yaml`` in the project root.

    Returns:
        The parsed config as a dict.
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with cfg_path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    """Check that required sections and per-instrument fields are present.

    Raises:
        ConfigError: If something required is missing or malformed.
    """
    if not isinstance(cfg, dict):
        raise ConfigError("config must be a mapping")
    missing = [s for s in _REQUIRED_SECTIONS if s not in cfg]
    if missing:
        raise ConfigError(f"config missing sections: {missing}")
    ZoneInfo(cfg["timezone"])  # raises if invalid
    for key in ("open_time", "close_time", "holidays_file"):
        if key not in cfg["market"]:
            raise ConfigError(f"market.{key} missing")
    for name, idx in cfg["indices"].items():
        if idx["ticker"] not in cfg["instruments"]:
            raise ConfigError(f"index {name} ticker {idx['ticker']} not in instruments")
    for ticker, inst in cfg["instruments"].items():
        for key in ("timezone", "close_time"):
            if key not in inst:
                raise ConfigError(f"instruments[{ticker}].{key} missing")
        ZoneInfo(inst["timezone"])
        parse_time(inst["close_time"])


def parse_time(value: str) -> time:
    """Parse an ``HH:MM`` string into a ``datetime.time``."""
    hours, minutes = str(value).split(":")
    return time(int(hours), int(minutes))


def ist(cfg: dict[str, Any]) -> ZoneInfo:
    """Return the project timezone (Asia/Kolkata)."""
    return ZoneInfo(cfg["timezone"])


def resolve_path(path: str | Path) -> Path:
    """Resolve a config path relative to the project root."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for scripts."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
