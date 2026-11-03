"""Range model, VIX baselines, gap models, and live prediction output tests."""

from __future__ import annotations

import copy
import importlib.util

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from backtest.range_eval import (beats_baseline, evaluate_range, interval_metrics, pinball_loss,
                                 range_report_markdown, range_training_frame)
from features.builder import build_features
from models.baselines import ThresholdRule, gap_baselines
from models.range import (VixEmpiricalRange, VixNormalRange, band_columns, column_quantiles,
                          make_consistent, range_model_from_config)
from settings import PROJECT_ROOT

BANDS = [0.68, 0.95]
COLS = ["lo95", "lo68", "med", "hi68", "hi95"]


@pytest.fixture(scope="module")
def rcfg(cfg, tmp_path_factory):
    c = copy.deepcopy(cfg)
    c["validation"].update(min_train_sessions=250, test_sessions=63, embargo_sessions=1)
    c["models"]["range"]["test_sessions"] = 126
    c["models"]["gap"]["candidates"] = ["logistic"]
    out = tmp_path_factory.mktemp("out")
    c["models"]["artifacts_dir"] = str(out / "artifacts")
    c["reporting"]["reports_dir"] = str(out / "reports")
    c["data"]["processed_dir"] = str(out / "processed")
    return c


@pytest.fixture(scope="module")
def fs_morning(market_bars, rcfg, calendar):
    return build_features(market_bars, rcfg, calendar, "nifty", "morning")


@pytest.fixture(scope="module")
def range_report(fs_morning, rcfg):
    return evaluate_range(fs_morning, rcfg)


# ---------------------------------------------------------------- helpers and metrics

def test_band_columns_and_levels():
    assert band_columns(BANDS) == COLS
    q = column_quantiles(BANDS)
    assert q["lo95"] == pytest.approx(0.025) and q["hi68"] == pytest.approx(0.84) and q["med"] == 0.5


def test_pinball_loss():
    y = np.array([1.0, 2.0])
    assert pinball_loss(y, np.array([1.5, 1.5]), 0.5) == pytest.approx(0.25)
    assert pinball_loss(y, np.array([0.0, 0.0]), 0.9) == pytest.approx(0.9 * 1.5)


def test_interval_metrics_coverage_and_width():
    y = pd.Series([0.0, 0.01, -0.02, 0.05])
    pred = pd.DataFrame({"lo95": -0.03, "lo68": -0.01, "med": 0.0, "hi68": 0.01, "hi95": 0.03}, index=y.index)
    m = interval_metrics(y, pred, BANDS)
    assert m["coverage_68"] == 0.5 and m["coverage_95"] == 0.75
    assert m["width_68_pct"] == pytest.approx((np.exp(0.01) - np.exp(-0.01)) * 100)


def test_make_consistent_orders_quantiles_and_targets():
    idx = [0]
    preds = {"y_open": pd.DataFrame([[0.0, 0.01, 0.005, 0.02, 0.03]], index=idx, columns=COLS),
             "y_high": pd.DataFrame([[-0.01, 0.0, 0.0, 0.01, 0.02]], index=idx, columns=COLS),
             "y_low": pd.DataFrame([[-0.03, -0.02, -0.01, 0.0, 0.04]], index=idx, columns=COLS)}
    out = make_consistent(preds, COLS)
    for df in out.values():
        assert (np.diff(df.to_numpy(), axis=1) >= 0).all()
    assert (out["y_high"].to_numpy() >= out["y_open"].to_numpy()).all()
    assert (out["y_low"].to_numpy() <= out["y_open"].to_numpy()).all()


def test_beats_baseline_rule():
    base = {"coverage_68": 0.80, "coverage_95": 0.99, "width_68_pct": 2.0, "width_95_pct": 4.0}
    good = {"coverage_68": 0.67, "coverage_95": 0.95, "width_68_pct": 1.0, "width_95_pct": 2.0}
    wide = dict(good, width_95_pct=4.5)
    undercover = dict(good, coverage_68=0.50)
    assert beats_baseline(good, base, BANDS, 0.01)
    assert not beats_baseline(wide, base, BANDS, 0.01)
    assert not beats_baseline(undercover, base, BANDS, 0.01)


# ---------------------------------------------------------------- baselines

def test_vix_normal_baseline_matches_formula(fs_morning, rcfg):
    X = fs_morning.features.dropna(subset=["indiavix_implied_move"]).tail(3)
    out = VixNormalRange(["y_open"], BANDS, "indiavix_implied_move").predict(X)["y_open"]
    s = X["indiavix_implied_move"]
    np.testing.assert_allclose(out["hi68"], norm.ppf(0.84) * s)
    np.testing.assert_allclose(out["lo95"], norm.ppf(0.025) * s)
    assert (out["med"] == 0).all()
    # The CLAUDE.md formula: Close * (VIX/100) / sqrt(252), as a fraction of the close.
    np.testing.assert_allclose(s, X["indiavix_level"] / 100 / np.sqrt(252))


def test_vix_empirical_baseline_uses_training_quantiles(fs_morning, rcfg):
    X, Y = range_training_frame(fs_morning, rcfg)
    m = VixEmpiricalRange(["y_high"], BANDS, "indiavix_implied_move").fit(X, Y)
    z = (Y["y_high"] / X["indiavix_implied_move"]).dropna()
    assert m.z_quantiles_["y_high"]["med"] == pytest.approx(np.quantile(z, 0.5))


# ---------------------------------------------------------------- range model

def test_range_model_calibrated_out_of_sample(range_report):
    for t in ("y_open", "y_high", "y_low"):
        m = range_report.metrics["model"][t]
        assert abs(m["coverage_68"] - 0.68) < 0.08, (t, m)
        assert abs(m["coverage_95"] - 0.95) < 0.04, (t, m)


def test_range_report_contents(range_report):
    md = range_report_markdown("Range: test", range_report)
    assert "baseline_vix_normal" in md and "baseline_vix_empirical" in md and "cov68" in md
    assert set(range_report.use_model) == {"y_open", "y_high", "y_low"}
    assert "vix_high" in range_report.splits["model"]["y_open"] or \
        "vix_normal" in range_report.splits["model"]["y_open"]


def test_range_predictions_unaffected_by_later_data(fs_morning, rcfg):
    """Walk-forward range predictions for early folds must not change when later rows change."""
    base = evaluate_range(fs_morning, rcfg)
    first = base.predictions["model"]["y_open"]
    cut_fold = 1
    last_date = first[first["fold"] == cut_fold].index.max()
    tampered = copy.copy(fs_morning)
    later = fs_morning.features.index > last_date
    feats = fs_morning.features.copy()
    feats.loc[later] = feats.loc[later] * 3.0
    targs = fs_morning.targets.copy()
    targs.loc[later, ["y_open", "y_high", "y_low"]] *= -2.0
    tampered.features, tampered.targets = feats, targs
    redo = evaluate_range(tampered, rcfg).predictions["model"]
    for t, df in base.predictions["model"].items():
        keep = df["fold"] <= cut_fold
        pd.testing.assert_frame_equal(redo[t][keep].drop(columns="y"), df[keep].drop(columns="y"))


def test_range_model_handles_missing_vix_with_fallback(fs_morning, rcfg):
    X, Y = range_training_frame(fs_morning, rcfg)
    m = range_model_from_config(rcfg).fit(X, Y)
    row = X.tail(1).copy()
    row["indiavix_implied_move"] = np.nan
    out = m.predict(row)
    assert out["y_open"].notna().all(axis=None)  # falls back to idx_vol_20


# ---------------------------------------------------------------- gap

def test_threshold_rule_and_gap_baselines():
    X = pd.DataFrame({"idx_gap": [0.01, -0.01, 0.0, np.nan], "gspc_ret_1": [0.01, -0.01, 0.0, 0.01]})
    y = pd.Series([1, 0, 0, 1])
    up = ThresholdRule("prev", "idx_gap", np.log1p(0.002)).fit(X, y)
    assert list(up.signal(X).iloc[:3]) == [True, False, False]
    assert set(gap_baselines("down", 0.002)) == {"base_rate", "previous_gap", "us_overnight"}
    down = gap_baselines("down", 0.002)["us_overnight"]()
    assert down.signal(X).iloc[1] is True or down.signal(X).iloc[1] == True  # noqa: E712


# ---------------------------------------------------------------- end to end (scripts)

def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_retrain_and_live_outputs(fs_morning, rcfg, tmp_path):
    from pathlib import Path

    retrain = _load_script("retrain")
    daily = _load_script("daily_update")
    reports = Path(rcfg["reporting"]["reports_dir"])
    reports.mkdir(parents=True, exist_ok=True)
    retrain.retrain_gap(fs_morning, rcfg, "nifty", "morning", reports)
    retrain.retrain_range(fs_morning, rcfg, "nifty", "morning", reports)
    assert (reports / "range_nifty_morning.md").exists() and (reports / "gap_nifty_morning.md").exists()

    live = copy.copy(fs_morning)
    live.features, live.meta = fs_morning.features.tail(1), fs_morning.meta.tail(1)
    gap = daily.predict_gap(rcfg, "nifty", "morning", live)
    assert gap["p_gap_up"] + gap["p_gap_flat"] + gap["p_gap_down"] == pytest.approx(1.0, abs=1e-3)
    rng = daily.predict_range(rcfg, "nifty", "morning", live)
    for t in ("open", "high", "low"):
        vals = [rng[f"{t}_{c}"] for c in COLS]
        assert vals == sorted(vals), (t, vals)
        assert rng[f"{t}_source"] in ("model", "vix_baseline")
    assert rng["high_med"] >= rng["open_med"] >= rng["low_med"]

    # Predictions log gains new columns without losing old rows.
    p1 = daily.append_prediction(rcfg, {"target_date": "2026-11-04", "p_up": 0.6})
    daily.append_prediction(rcfg, {"target_date": "2026-11-05", "p_up": 0.4, **gap})
    log = pd.read_csv(p1)
    assert len(log) == 2 and "p_gap_up" in log and log["p_gap_up"].isna().iloc[0]
