"""Direction model, baselines, walk-forward validation and reporting tests."""

from __future__ import annotations

import copy
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backtest.direction_eval import evaluate_direction, report_markdown, report_to_dict, training_frame
from backtest.metrics import classification_metrics, expected_calibration_error, vix_regime
from backtest.walkforward import walk_forward_predict, walk_forward_splits
from features.builder import build_features
from models.artifacts import load_artifact, save_artifact
from models.baselines import AlwaysUp, EmaCrossover, PreviousDay
from models.direction import DirectionModel, direction_model_from_config
from settings import PROJECT_ROOT


@pytest.fixture(scope="module")
def mcfg(cfg):
    """Config sized for ~2.8 years of synthetic data."""
    c = copy.deepcopy(cfg)
    c["validation"].update(min_train_sessions=250, test_sessions=63, embargo_sessions=1)
    c["models"]["direction"]["candidates"] = ["logistic", "lightgbm"]
    return c


# ---------------------------------------------------------------- walk-forward

def test_walk_forward_splits_are_time_ordered():
    folds = walk_forward_splits(1000, min_train=500, test_size=100, embargo=2)
    assert len(folds) == 5
    seen = []
    for f in folds:
        assert f.train_idx[0] == 0                       # expanding window
        assert f.train_idx.max() + 2 < f.test_idx.min()  # embargo respected
        seen.extend(f.test_idx)
    assert seen == list(range(500, 1000))                # every test row once, in order


def test_rolling_window_caps_training_size():
    folds = walk_forward_splits(1000, 300, 100, 0, max_train=300)
    assert all(len(f.train_idx) <= 300 for f in folds)
    assert folds[-1].train_idx[0] == 600


def test_walk_forward_rejects_unsorted_rows():
    X = pd.DataFrame({"a": range(10)}, index=pd.date_range("2026-01-01", periods=10)[::-1])
    with pytest.raises(ValueError):
        walk_forward_predict(X, pd.Series(0, index=X.index), AlwaysUp, walk_forward_splits(10, 5, 2))


def test_no_shuffled_splits_anywhere_in_code():
    """Rule 2: never shuffle, never use train_test_split."""
    offenders = []
    for path in PROJECT_ROOT.rglob("*.py"):
        if "tests" in path.parts or ".venv" in path.parts:
            continue
        text = path.read_text()
        if re.search(r"train_test_split|shuffle\s*=\s*True|KFold\(", text):
            offenders.append(str(path))
    assert not offenders, offenders


def test_model_predictions_unaffected_by_later_data(market_bars, mcfg, calendar):
    """Preprocessing and calibration must only see each fold's training rows: altering
    rows after a fold's test block must not change that fold's predictions."""
    fs = build_features(market_bars, mcfg, calendar, "nifty", "morning")
    X, y = training_frame(fs, mcfg)
    folds = walk_forward_splits(len(X), 250, 63, 1)
    k = 2
    cut = folds[k].test_idx.max() + 1
    Xt, yt = X.copy(), y.copy()
    rng = np.random.default_rng(0)
    Xt.iloc[cut:] = Xt.iloc[cut:] * rng.uniform(-5, 5, size=Xt.iloc[cut:].shape)
    yt.iloc[cut:] = 1 - yt.iloc[cut:]
    for est in ("logistic", "lightgbm"):
        def make(est=est):
            return direction_model_from_config(mcfg, est)
        a = walk_forward_predict(X, y, make, folds[: k + 1])
        b = walk_forward_predict(Xt, yt, make, folds[: k + 1])
        pd.testing.assert_frame_equal(a, b)


# ---------------------------------------------------------------- baselines

def frame(ret, ema):
    return pd.DataFrame({"idx_ret_1": ret, "idx_ema20_50": ema})


def test_always_up_predicts_up_with_base_rate():
    X = frame([0.1] * 10, [0.0] * 10)
    y = pd.Series([1] * 7 + [0] * 3)
    p = AlwaysUp().fit(X, y).predict_proba(X)[:, 1]
    assert np.allclose(p, 8 / 12)  # Laplace-smoothed up-rate
    assert classification_metrics(y, p)["accuracy"] == 0.7


def test_previous_day_and_ema_rules_use_training_rates():
    X = frame([0.01, -0.01, 0.02, -0.02, np.nan], [1, 1, -1, -1, np.nan])
    y = pd.Series([1, 0, 1, 0, 1])
    pd_model = PreviousDay().fit(X, y)
    p = pd_model.predict_proba(X)[:, 1]
    assert p[0] == pytest.approx(3 / 4) and p[1] == pytest.approx(1 / 4)
    assert p[4] == pytest.approx(pd_model.base_rate_)  # NaN signal -> base rate
    e = EmaCrossover().fit(X, y).predict_proba(X)[:, 1]
    assert e[0] == e[1] and e[2] == e[3]


# ---------------------------------------------------------------- metrics

def test_log_loss_improvement_sign_and_t():
    from backtest.direction_eval import log_loss_improvement
    rng = np.random.default_rng(0)
    y = pd.Series(rng.integers(0, 2, 2000))
    good = pd.Series(np.clip(np.where(y == 1, 0.65, 0.35) + rng.normal(0, 0.1, 2000), 0.05, 0.95))
    flat = pd.Series(np.full(2000, 0.5))
    gain, t = log_loss_improvement(y, good, flat)
    assert gain > 0 and t > 10
    gain, t = log_loss_improvement(y, flat, good)
    assert gain < 0


def test_metrics_known_values():
    y = pd.Series([1, 0, 1, 0])
    p = pd.Series([0.9, 0.1, 0.4, 0.6])
    m = classification_metrics(y, p)
    assert m["accuracy"] == 0.5 and m["precision"] == 0.5 and m["recall"] == 0.5
    assert m["roc_auc"] == 0.75
    assert m["brier"] == pytest.approx((0.01 + 0.01 + 0.36 + 0.36) / 4)


def test_ece_zero_for_perfect_calibration():
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 1, 200_000)
    y = (rng.uniform(0, 1, p.size) < p).astype(int)
    assert expected_calibration_error(pd.Series(y), pd.Series(p)) < 0.01


def test_vix_regime_labels():
    r = vix_regime(pd.Series([10, 15, 25, np.nan]), 13, 20)
    assert list(r) == ["low", "normal", "high", "unknown"]


# ---------------------------------------------------------------- end to end

def test_random_walk_gives_no_edge(market_bars, mcfg, calendar):
    """Independent random walks: an honest pipeline must find nothing."""
    fs = build_features(market_bars, mcfg, calendar, "nifty", "morning")
    rep = evaluate_direction(fs, mcfg)
    for name in ("model_logistic", "model_lightgbm"):
        m = rep.metrics[name]
        assert m["accuracy"] < 0.6, m
        assert abs(m["roc_auc"] - 0.5) < 0.1, m
    assert not any("probable leak" in w for w in rep.warnings)
    assert not any(rep.beats_baseline.values())  # luck must not count as beating a baseline
    assert {"vix_low", "vix_normal", "vix_high", "is_expiry"} <= set(rep.splits["model_lightgbm"])


def test_planted_overnight_signal_found_in_morning_only(signal_bars, mcfg, calendar):
    """Nifty follows the previous US session, which closes ~02:30 IST. The morning model
    must find it (and trip the >60% accuracy alarm); the evening model must not."""
    morning = evaluate_direction(build_features(signal_bars, mcfg, calendar, "nifty", "morning"), mcfg)
    evening = evaluate_direction(build_features(signal_bars, mcfg, calendar, "nifty", "evening"), mcfg)
    for name in ("model_logistic", "model_lightgbm"):
        assert morning.metrics[name]["roc_auc"] > 0.75
        assert morning.beats_baseline[name]
        assert abs(evening.metrics[name]["roc_auc"] - 0.5) < 0.1
    assert any("probable leak" in w for w in morning.warnings)
    assert not any("probable leak" in w for w in evening.warnings)


def test_report_outputs(market_bars, mcfg, calendar):
    fs = build_features(market_bars, mcfg, calendar, "sensex", "evening")
    rep = evaluate_direction(fs, mcfg, candidates=["xgboost"])
    d = report_to_dict(rep)
    assert d["n_test"] == len(rep.predictions) and d["best_baseline"].startswith("baseline_")
    assert set(rep.predictions.columns) >= {"y", "fold", "p_model_xgboost", "p_baseline_always_up",
                                             "p_baseline_previous_day", "p_baseline_ema_20_50"}
    md = report_markdown("Direction: sensex", rep)
    assert "| model_xgboost |" in md and "vix_high" in md


def test_calibration_learned_from_training_window_only(market_bars, mcfg, calendar):
    fs = build_features(market_bars, mcfg, calendar, "nifty", "evening")
    X, y = training_frame(fs, mcfg)
    m = DirectionModel("logistic", {"C": 0.05, "max_iter": 5000}, "sigmoid", 0.2).fit(X, y)
    assert m.calibrator_ is not None
    p = m.predict_proba(X)[:, 1]
    assert ((p > 0) & (p < 1)).all()
    tiny = DirectionModel("logistic", {}, "sigmoid", 0.2).fit(X.iloc[:100], y.iloc[:100])
    assert tiny.calibrator_ is None  # too few rows to calibrate


def test_artifact_round_trip(market_bars, mcfg, calendar, tmp_path):
    fs = build_features(market_bars, mcfg, calendar, "nifty", "evening")
    X, y = training_frame(fs, mcfg)
    m = direction_model_from_config(mcfg, "lightgbm").fit(X, y)
    path = Path(tmp_path) / "m.joblib"
    save_artifact(path, m, {"features": list(X.columns)})
    loaded, meta = load_artifact(path)
    assert meta["features"] == list(X.columns) and "saved_at" in meta
    np.testing.assert_allclose(loaded.predict_proba(X.tail(5)), m.predict_proba(X.tail(5)))
    # Missing columns at prediction time are treated as NaN, not an error.
    assert loaded.predict_proba(X.tail(1).drop(columns=["idx_rsi_14"])).shape == (1, 2)
    assert load_artifact(Path(tmp_path) / "none.joblib") is None
    assert m.feature_importance().sum() == pytest.approx(1.0)
