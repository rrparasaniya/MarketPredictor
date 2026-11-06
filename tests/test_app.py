"""Dashboard data-layer tests and a headless render of the Streamlit app."""

from __future__ import annotations

import copy
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
import yaml

from app.data_access import (DISCLAIMER, dashboard_state, day_label, load_predictions, range_frame,
                             track_record)
from settings import PROJECT_ROOT

IST = ZoneInfo("Asia/Kolkata")


def pred_row(index="nifty", target="2026-11-04", created="2026-11-03T16:20:00+05:30", run="evening",
             p_up=0.6, prev_close=23810.85):
    row = {"created_at": created, "target_date": target, "label": "tomorrow", "index": index, "run": run,
           "p_up": p_up, "call": "up" if p_up >= 0.5 else "down", "decision_threshold": 0.5,
           "cutoff": created, "prev_session": "2026-11-03", "prev_close": prev_close,
           "model_estimator": "lightgbm", "model_trained_through": "2026-11-03",
           "model_beats_baseline": False, "p_gap_up": 0.5, "p_gap_flat": 0.35, "p_gap_down": 0.15,
           "gap_model_beats_baseline": True, "data_refresh_ok": True}
    for t, (m, w) in {"open": (1.0005, 0.004), "high": (1.003, 0.006), "low": (0.997, 0.006)}.items():
        row[f"{t}_source"] = "model"
        for b, k in (("lo95", -2), ("lo68", -1), ("med", 0), ("hi68", 1), ("hi95", 2)):
            row[f"{t}_{b}"] = round(prev_close * (m + k * w / 2), 2)
    return row


@pytest.fixture
def app_cfg(cfg, tmp_path):
    c = copy.deepcopy(cfg)
    c["data"]["processed_dir"] = str(tmp_path / "processed")
    c["data"]["cache_dir"] = str(tmp_path / "raw")
    c["reporting"]["reports_dir"] = str(tmp_path / "reports")
    (tmp_path / "processed").mkdir()
    rows = [pred_row(), pred_row("sensex", prev_close=76917.85),
            pred_row(created="2026-11-04T08:45:00+05:30", run="morning", p_up=0.4)]
    pd.DataFrame(rows).to_csv(tmp_path / "processed" / "predictions.csv", index=False)
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(c))
    c["_path"] = str(path)
    return c


def test_day_label():
    today = date(2026, 11, 6)
    assert day_label(date(2026, 11, 6), today) == "today"
    assert day_label(date(2026, 11, 7), today) == "tomorrow"
    assert day_label(date(2026, 11, 9), today) == "next session (Monday)"
    assert day_label(date(2026, 11, 5), today) == "past session"


def test_state_prefers_latest_run_for_target(app_cfg, calendar):
    preds = load_predictions(app_cfg)
    st = dashboard_state(app_cfg, calendar, datetime(2026, 11, 4, 9, 0, tzinfo=IST), preds)
    assert st.target.target_date == date(2026, 11, 4)
    assert st.latest["nifty"]["run"] == "morning"      # created later than the evening one
    assert st.latest["sensex"]["run"] == "evening"
    assert "open" in st.market_note.lower() or "9:15" in st.market_note


def test_state_flags_stale_predictions(app_cfg, calendar):
    preds = load_predictions(app_cfg)
    st = dashboard_state(app_cfg, calendar, datetime(2026, 11, 4, 17, 0, tzinfo=IST), preds)
    assert st.target.target_date == date(2026, 11, 5)
    assert st.latest["nifty"] is None and st.stale["nifty"] is not None


def test_range_frame_ordering(app_cfg):
    rf = range_frame(load_predictions(app_cfg).iloc[0])
    assert list(rf["target"]) == ["Open", "High", "Low"]
    assert (rf[["lo95", "lo68", "med", "hi68", "hi95"]].diff(axis=1).iloc[:, 1:] > 0).all(axis=None)


def test_track_record_scores_forecasts(app_cfg):
    preds = load_predictions(app_cfg)
    idx = pd.DatetimeIndex(["2026-11-04"], tz=IST)
    bars = {"nifty": pd.DataFrame({"open": [23830.0], "high": [23900.0], "low": [23700.0],
                                   "close": [23750.0]}, index=idx)}
    tr = track_record(preds, bars, app_cfg)
    assert len(tr) == 1
    r = tr.iloc[0]
    assert r["run"] == "morning" and r["call"] == "down" and r["actual"] == "down" and r["direction_correct"]
    assert r["gap_actual"] == "flat" and r["gap_call"] == "up"
    assert r["open_in_95"]


def test_load_predictions_missing_file(cfg, tmp_path):
    c = copy.deepcopy(cfg)
    c["data"]["processed_dir"] = str(tmp_path / "nothing")
    assert load_predictions(c).empty


@pytest.mark.parametrize("now,expect", [
    ("2026-11-04T09:00:00+05:30", "Prediction for: Wed 04 Nov 2026, today"),
    ("2026-11-03T18:00:00+05:30", "Prediction for: Wed 04 Nov 2026, tomorrow"),
])
def test_app_renders_required_elements(app_cfg, monkeypatch, now, expect):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("MARKETPREDICTOR_CONFIG", app_cfg["_path"])
    monkeypatch.setenv("MARKETPREDICTOR_NOW", now)
    at = AppTest.from_file(str(PROJECT_ROOT / "app" / "main.py"), default_timeout=60)
    at.run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert expect in text
    assert "Last updated:" in text
    assert DISCLAIMER in [w.value for w in at.warning] and DISCLAIMER in text
    assert any("Low reliability" in w.value for w in at.warning)
    assert any("In short:" in i.value for i in at.info)
    assert "How will the market open?" in [h.value for h in at.subheader]


def test_app_shows_stale_notice(app_cfg, monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("MARKETPREDICTOR_CONFIG", app_cfg["_path"])
    monkeypatch.setenv("MARKETPREDICTOR_NOW", "2026-11-04T17:00:00+05:30")
    at = AppTest.from_file(str(PROJECT_ROOT / "app" / "main.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert any("forecast for 05 Nov isn't ready yet" in e.value for e in at.error)
