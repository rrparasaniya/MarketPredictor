"""End-to-end checks of scripts/daily_update.py against synthetic data (no network)."""

from __future__ import annotations

import copy
import importlib.util
import logging
from datetime import date

import pandas as pd
import pytest
import yaml

from settings import PROJECT_ROOT
from tests.conftest import FakeSource, make_bars


def _load(name):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def run_daily(cfg, calendar, tmp_path, monkeypatch):
    """Run daily_update.main at a given time on synthetic bars up to 5 Nov 2026."""
    nse = calendar.trading_days(date(2025, 6, 2), date(2026, 11, 5))
    wk = pd.bdate_range("2025-06-02", "2026-11-05")
    data = {t: make_bars(nse if i["timezone"] == "Asia/Kolkata" else wk, 100.0 * (k + 1), k)
            for k, (t, i) in enumerate(cfg["instruments"].items())}
    c = copy.deepcopy(cfg)
    c["data"].update(cache_dir=str(tmp_path / "raw"), processed_dir=str(tmp_path / "processed"),
                     history_start="2025-06-02")
    c["models"]["artifacts_dir"] = str(tmp_path / "artifacts")  # no models: nothing is written
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(c))
    monkeypatch.setattr("data.store.get_source", lambda _cfg: FakeSource(data))
    daily = _load("daily_update")

    def run(now: str) -> int:
        return daily.main(["--config", str(path), "--now", now])
    return run


def test_run_before_days_bar_is_final_skips_forecast(run_daily, caplog):
    with caplog.at_level(logging.INFO):
        assert run_daily("2026-11-05T15:31:00+05:30") == 0
    assert "latest final bar is 2026-11-04, not the session before 2026-11-06" in caplog.text
    assert "using the evening models" in caplog.text


def test_run_after_bar_is_final_builds_forecast(run_daily, caplog):
    with caplog.at_level(logging.INFO):
        assert run_daily("2026-11-05T16:20:00+05:30") == 0
    assert "skipping this forecast" not in caplog.text
    assert "prev_session=2026-11-05" in caplog.text


def test_late_night_pre_open_run_uses_evening_models(run_daily, caplog):
    with caplog.at_level(logging.INFO):
        assert run_daily("2026-11-05T00:01:00+05:30") == 0
    assert "mode=pre_open" in caplog.text and "using the evening models" in caplog.text
