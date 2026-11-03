"""Data the dashboard shows: latest predictions, track record, and model quality.

Pure functions (no Streamlit), so they can be unit-tested.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

from data.calendar import TradingCalendar
from data.timing import PredictionMode, PredictionTarget, resolve_prediction_target
from settings import resolve_path

DISCLAIMER = "For educational purposes only. Not investment advice. Not SEBI-registered."
BANDS = ("lo95", "lo68", "med", "hi68", "hi95")


def load_predictions(cfg: dict[str, Any]) -> pd.DataFrame:
    """The predictions log written by ``daily_update.py`` (empty frame if none yet)."""
    path = resolve_path(cfg["data"]["processed_dir"]) / "predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert(cfg["timezone"])
    df["target_date"] = pd.to_datetime(df["target_date"]).dt.date
    return df.sort_values("created_at").reset_index(drop=True)


def day_label(target: date, today: date) -> str:
    """"today", "tomorrow", or the weekday for later sessions (relative to *now*)."""
    days = (target - today).days
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    if days > 1:
        return f"next session ({target.strftime('%A')})"
    return "past session"


@dataclass
class DashboardState:
    """What the dashboard should display right now."""

    target: PredictionTarget
    latest: dict[str, pd.Series | None]   # index name -> latest prediction for the target
    stale: dict[str, pd.Series | None]    # index name -> most recent older prediction, if no current one
    market_note: str


def market_note(target: PredictionTarget) -> str:
    """One line explaining what the dashboard is showing, by time of day."""
    return {
        PredictionMode.PRE_OPEN: "Before the 9:15 open: forecasts for today's session.",
        PredictionMode.INTRADAY: "Market is open: showing today's forecast (no new forecast until after 3:30 PM).",
        PredictionMode.POST_CLOSE: "After the 3:30 PM close: forecasts for the next trading session.",
        PredictionMode.NON_TRADING_DAY: "Market closed today: forecasts for the next trading session.",
    }[target.mode]


def dashboard_state(cfg: dict[str, Any], calendar: TradingCalendar, now: datetime,
                    preds: pd.DataFrame) -> DashboardState:
    """Pick the prediction to show per index for the session being forecast now.

    When both runs exist for the target, the most recently created one wins (the
    morning run has fresher overnight data than the previous evening's).
    """
    target = resolve_prediction_target(now, calendar, cfg)
    latest: dict[str, pd.Series | None] = {}
    stale: dict[str, pd.Series | None] = {}
    for name in cfg["indices"]:
        rows = preds[preds["index"] == name] if not preds.empty else preds
        cur = rows[rows["target_date"] == target.target_date] if not rows.empty else rows
        latest[name] = cur.iloc[-1] if len(cur) else None
        stale[name] = rows.iloc[-1] if latest[name] is None and len(rows) else None
    return DashboardState(target, latest, stale, market_note(target))


def range_frame(pred: pd.Series) -> pd.DataFrame:
    """Open/high/low bands from a prediction row, one row per target."""
    rows = []
    for t in ("open", "high", "low"):
        if f"{t}_med" not in pred or pd.isna(pred.get(f"{t}_med")):
            continue
        rows.append({"target": t.capitalize(), "source": pred.get(f"{t}_source", ""),
                     **{b: float(pred[f"{t}_{b}"]) for b in BANDS}})
    return pd.DataFrame(rows)


def track_record(preds: pd.DataFrame, bars: dict[str, pd.DataFrame], cfg: dict[str, Any]) -> pd.DataFrame:
    """Past forecasts next to what actually happened.

    One row per index and target session (the latest forecast made for it).
    """
    if preds.empty:
        return pd.DataFrame()
    last = preds.groupby(["index", "target_date"], as_index=False).tail(1)
    gap_thr = float(cfg["prediction"]["gap_threshold"])
    out = []
    for _, p in last.iterrows():
        b = bars.get(p["index"])
        if b is None or b.empty:
            continue
        day = b[b.index.date == p["target_date"]]
        if day.empty:
            continue
        o, h, l, c = (float(day[k].iloc[0]) for k in ("open", "high", "low", "close"))
        pc = float(p["prev_close"])
        actual_up = c > pc * (1 + float(cfg["prediction"]["direction_threshold"]))
        gap = o / pc - 1
        actual_gap = "up" if gap > gap_thr else "down" if gap < -gap_thr else "flat"
        row = {"index": p["index"], "session": p["target_date"], "run": p["run"],
               "p_up": p["p_up"], "call": p["call"], "actual": "up" if actual_up else "down",
               "direction_correct": (p["call"] == "up") == actual_up,
               "close": c, "close_change_pct": (c / pc - 1) * 100}
        if "p_gap_up" in p and pd.notna(p.get("p_gap_up")):
            probs = {"up": p["p_gap_up"], "flat": p["p_gap_flat"], "down": p["p_gap_down"]}
            row.update(gap_call=max(probs, key=probs.get), gap_actual=actual_gap)
        for t, v in (("open", o), ("high", h), ("low", l)):
            if pd.notna(p.get(f"{t}_lo68")):
                row[f"{t}_in_68"] = bool(p[f"{t}_lo68"] <= v <= p[f"{t}_hi68"])
                row[f"{t}_in_95"] = bool(p[f"{t}_lo95"] <= v <= p[f"{t}_hi95"])
        out.append(row)
    return pd.DataFrame(out).sort_values("session", ascending=False) if out else pd.DataFrame()


def model_quality(cfg: dict[str, Any], index_name: str, run: str) -> dict[str, Any]:
    """Out-of-sample summary from the latest reports (empty dict if not generated yet)."""
    reports = resolve_path(cfg["reporting"]["reports_dir"])

    def read(name: str) -> dict[str, Any] | None:
        p = reports / f"{name}_{index_name}_{run}.json"
        return json.loads(p.read_text()) if p.exists() else None

    out: dict[str, Any] = {}
    est = cfg["models"]["direction"]["estimator"]
    if (d := read("direction")):
        m = d["metrics"].get(f"model_{est}", {})
        base = d["metrics"].get(d.get("best_baseline") or "", {})
        out["direction"] = {"period": f"{d['test_start']} to {d['test_end']}", "sessions": d["n_test"],
                            "accuracy": m.get("accuracy"), "roc_auc": m.get("roc_auc"),
                            "best_baseline": (d.get("best_baseline") or "").removeprefix("baseline_"),
                            "baseline_accuracy": base.get("accuracy"),
                            "beats_baseline": d["beats_baseline"].get(f"model_{est}")}
    if (g := read("gap")):
        gest = cfg["models"]["gap"]["estimator"]
        out["gap"] = {side: {"roc_auc": g[side]["metrics"].get(f"model_{gest}", {}).get("roc_auc"),
                             "beats_baseline": g[side]["beats_baseline"].get(f"model_{gest}")}
                      for side in ("up", "down") if side in g}
    if (r := read("range")):
        out["range"] = {t.removeprefix("y_"): {
            "coverage_68": r["metrics"]["model"][t]["coverage_68"],
            "coverage_95": r["metrics"]["model"][t]["coverage_95"],
            "width_68_pct": r["metrics"]["model"][t]["width_68_pct"],
            "vix_width_68_pct": r["metrics"]["baseline_vix_normal"][t]["width_68_pct"],
            "uses_model": r["use_model"][t]} for t in r["metrics"]["model"]}
    if (b := read("backtest")):
        m = b.get("model", {})
        out["backtest"] = {"cagr": m.get("cagr"), "sharpe": m.get("sharpe_idle_cash_0"),
                           "max_drawdown": m.get("max_drawdown"), "hit_rate": m.get("hit_rate"),
                           "buy_and_hold_cagr": b.get("buy_and_hold", {}).get("cagr")}
    return out


def fmt_pct(v: Any, digits: int = 1) -> str:
    """Format a fraction as a percentage, or an em dash if missing."""
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v * 100:.{digits}f}%"
