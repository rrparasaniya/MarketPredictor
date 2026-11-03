"""Optional CSV inputs and config validation tests."""

import copy

import pytest

from data.optional_inputs import load_all_optional_inputs, load_optional_input
from settings import ConfigError, validate_config


def with_input(cfg, path, **extra):
    spec = {"path": str(path), "date_column": "date", "available_time": "18:00", **extra}
    return dict(cfg, optional_inputs={"pcr_oi": spec})


def test_missing_optional_file_is_skipped(cfg, tmp_path):
    assert load_optional_input("pcr_oi", with_input(cfg, tmp_path / "nope.csv")) is None
    assert load_optional_input("not_configured", cfg) is None


def test_optional_file_loaded_with_availability(cfg, tmp_path):
    p = tmp_path / "pcr.csv"
    p.write_text("date,pcr\n2026-11-02,0.91\n2026-11-03,1.05\n")
    df = load_optional_input("pcr_oi", with_input(cfg, p))
    assert list(df["pcr"]) == [0.91, 1.05]
    assert str(df.index.tz) == "Asia/Kolkata"
    assert df["available_at"].iloc[0].isoformat() == "2026-11-02T18:00:00+05:30"


def test_explicit_available_at_column(cfg, tmp_path):
    p = tmp_path / "pcr.csv"
    p.write_text("date,pcr,available_at\n2026-11-02,0.9,2026-11-02T19:10:00+05:30\n")
    df = load_optional_input("pcr_oi", with_input(cfg, p))
    assert df["available_at"].iloc[0].isoformat() == "2026-11-02T19:10:00+05:30"


def test_malformed_optional_file_is_skipped(cfg, tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("when,pcr\nyesterday,1\n")
    assert load_optional_input("pcr_oi", with_input(cfg, p)) is None


def test_load_all_skips_missing(cfg):
    # The repo ships no optional CSVs.
    assert isinstance(load_all_optional_inputs(cfg), dict)


def test_config_validates(cfg):
    validate_config(cfg)


def test_config_rejects_index_without_instrument(cfg):
    bad = copy.deepcopy(cfg)
    del bad["instruments"]["^NSEI"]
    with pytest.raises(ConfigError):
        validate_config(bad)


def test_config_rejects_instrument_without_close_time(cfg):
    bad = copy.deepcopy(cfg)
    del bad["instruments"]["^GSPC"]["close_time"]
    with pytest.raises(ConfigError):
        validate_config(bad)


def test_all_planned_tickers_configured(cfg):
    expected = {"^NSEI", "^BSESN", "^NSEBANK", "^INDIAVIX", "INR=X", "BZ=F", "GC=F",
                "^TNX", "DX-Y.NYB", "^GSPC", "^IXIC", "^N225", "^HSI"}
    assert expected <= set(cfg["instruments"])
