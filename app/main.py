"""MarketPredictor dashboard: next-session forecasts for NIFTY 50 and SENSEX.

Run with:  streamlit run app/main.py
Env overrides (for testing): MARKETPREDICTOR_CONFIG (config path),
MARKETPREDICTOR_NOW (ISO timestamp with offset).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data_access import (DISCLAIMER, dashboard_state, day_label, fmt_pct,  # noqa: E402
                             load_predictions, model_quality, range_frame, track_record)
from data.calendar import TradingCalendar  # noqa: E402
from data.store import MarketDataStore  # noqa: E402
from settings import ist, load_config  # noqa: E402

# Colors (validated: ordinal blue pair for bands; diverging blue/gray/red for gap).
BAND_95, BAND_68, MEDIAN = "#86b6ef", "#2a78d6", "#ffffff"
GAP_COLORS = {"Gap up": "#2a78d6", "Flat": "#a3a29b", "Gap down": "#e34948"}
REFERENCE = "#8a8985"

st.set_page_config(page_title="MarketPredictor", page_icon="📈", layout="centered")


@st.cache_resource
def _setup():
    cfg = load_config(os.environ.get("MARKETPREDICTOR_CONFIG"))
    return cfg, TradingCalendar.from_config(cfg)


def _now(cfg) -> datetime:
    override = os.environ.get("MARKETPREDICTOR_NOW")
    return datetime.fromisoformat(override) if override else datetime.now(ist(cfg))


def gap_chart(pred: pd.Series) -> alt.Chart:
    """100% stacked bar: P(gap up / flat / down), with a 2px surface gap between segments."""
    df = pd.DataFrame({"outcome": list(GAP_COLORS),
                       "p": [pred["p_gap_up"], pred["p_gap_flat"], pred["p_gap_down"]]})
    df["order"] = range(len(df))
    df["label"] = df["outcome"] + " " + (df["p"] * 100).round().astype(int).astype(str) + "%"
    base = alt.Chart(df).encode(
        x=alt.X("sum(p):Q", stack="normalize", axis=None),
        order=alt.Order("order:Q"),
        tooltip=[alt.Tooltip("outcome:N", title="Opening"), alt.Tooltip("p:Q", title="Probability", format=".0%")])
    bars = base.mark_bar(height=28, cornerRadius=4).encode(
        color=alt.Color("outcome:N", scale=alt.Scale(domain=list(GAP_COLORS), range=list(GAP_COLORS.values())),
                        legend=None))
    return bars.properties(height=36)


def range_chart(rf: pd.DataFrame, prev_close: float) -> alt.Chart:
    """Interval chart: 95% band (light), 68% band (dark), median tick, previous close rule."""
    order = ["Open", "High", "Low"]
    y = alt.Y("target:N", sort=order, title=None)
    tip = [alt.Tooltip("target:N", title="Price"), alt.Tooltip("med:Q", title="Median", format=",.0f"),
           alt.Tooltip("lo68:Q", title="68% low", format=",.0f"), alt.Tooltip("hi68:Q", title="68% high", format=",.0f"),
           alt.Tooltip("lo95:Q", title="95% low", format=",.0f"), alt.Tooltip("hi95:Q", title="95% high", format=",.0f")]
    base = alt.Chart(rf).encode(y=y, tooltip=tip)
    b95 = base.mark_bar(color=BAND_95, height=14, cornerRadius=4).encode(
        x=alt.X("lo95:Q", title="Index level", scale=alt.Scale(zero=False), axis=alt.Axis(format=",.0f", grid=False)),
        x2="hi95:Q")
    b68 = base.mark_bar(color=BAND_68, height=14, cornerRadius=4).encode(x="lo68:Q", x2="hi68:Q")
    med = base.mark_tick(color=MEDIAN, thickness=2, size=14).encode(x="med:Q")
    rule = alt.Chart(pd.DataFrame({"prev_close": [prev_close]})).mark_rule(
        color=REFERENCE, strokeDash=[4, 4], strokeWidth=1.5).encode(
        x="prev_close:Q", tooltip=[alt.Tooltip("prev_close:Q", title="Previous close", format=",.2f")])
    return (b95 + b68 + med + rule).properties(height=150)


def show_index(name: str, label: str, pred: pd.Series, cfg) -> None:
    """Forecast panel for one index."""
    prev_close = float(pred["prev_close"])
    st.caption(f"Based on the {pd.Timestamp(pred['prev_session']).strftime('%d %b %Y')} close of "
               f"{prev_close:,.2f} · {pred['run']} run · data cutoff "
               f"{pd.Timestamp(pred['cutoff']).strftime('%d %b %H:%M IST')}")
    if not bool(pred.get("data_refresh_ok", True)):
        st.warning("Some market data failed to refresh for this run; older cached data was used.", icon="⚠️")

    st.subheader("Opening gap")
    if pd.notna(pred.get("p_gap_up")):
        thr = float(cfg["prediction"]["gap_threshold"]) * 100
        st.altair_chart(gap_chart(pred), width="stretch")
        st.markdown(f"🟦 **Gap up {float(pred['p_gap_up']):.0%}** &nbsp;·&nbsp; "
                    f"⬜ **Flat {float(pred['p_gap_flat']):.0%}** &nbsp;·&nbsp; "
                    f"🟥 **Gap down {float(pred['p_gap_down']):.0%}**")
        st.caption(f"Gap up / down = open more than {thr:.1f}% above / below the previous close.")
    else:
        st.info("No gap model trained yet.")

    st.subheader("Expected range")
    rf = range_frame(pred)
    if rf.empty:
        st.info("No range model trained yet.")
    else:
        st.altair_chart(range_chart(rf, prev_close), width="stretch")
        st.caption("Dark band: 68% range · light band: 95% range · white tick: median · dashed line: previous close.")
        table = pd.DataFrame({
            "": rf["target"],
            "Median": rf["med"].map("{:,.0f}".format),
            "68% range": rf["lo68"].map("{:,.0f}".format) + " – " + rf["hi68"].map("{:,.0f}".format),
            "95% range": rf["lo95"].map("{:,.0f}".format) + " – " + rf["hi95"].map("{:,.0f}".format),
        })
        st.dataframe(table, width="stretch", hide_index=True)
        if (rf["source"] == "vix_baseline").any():
            st.caption("Rows marked VIX baseline use the India-VIX-implied range because the ML range "
                       "did not beat it in testing.")

    st.subheader("Direction")
    p_up = float(pred["p_up"])
    c1, c2 = st.columns(2)
    c1.metric("Chance of closing above previous close", f"{p_up:.0%}")
    c2.metric("Call", "Up" if pred["call"] == "up" else "Down")
    if not bool(pred.get("model_beats_baseline", False)):
        st.warning("This direction model did not beat simple baselines in testing. Treat this as noise.",
                   icon="⚠️")
    st.caption("Direction forecasts come mostly from overnight global cues that the market prices in at "
               "the open. In backtests they showed no tradable edge after costs.")


def quality_section(cfg, name: str) -> None:
    """Out-of-sample track record from the walk-forward reports."""
    for run in ("morning", "evening"):
        q = model_quality(cfg, name, run)
        if not q:
            continue
        st.markdown(f"**{run.capitalize()} run**")
        lines = []
        if (d := q.get("direction")):
            lines.append(f"- Direction ({d['period']}, {d['sessions']:,} sessions): accuracy "
                         f"{fmt_pct(d['accuracy'])} vs {fmt_pct(d['baseline_accuracy'])} for the best simple "
                         f"rule ({d['best_baseline']}); {'beats' if d['beats_baseline'] else 'does not beat'} it.")
        if (g := q.get("gap")):
            lines.append("- Gap: ROC-AUC " + ", ".join(f"{s} {v['roc_auc']:.2f}" for s, v in g.items())
                         + " (0.5 = coin flip).")
        if (r := q.get("range")):
            lines.append("- Range coverage (68% / 95% bands): " + "; ".join(
                f"{t} {fmt_pct(v['coverage_68'], 0)} / {fmt_pct(v['coverage_95'], 0)}, 68% band "
                f"{v['width_68_pct']:.2f}% wide vs {v['vix_width_68_pct']:.2f}% for VIX" for t, v in r.items()))
        if (b := q.get("backtest")):
            lines.append(f"- Trading the direction call (open → close, after costs): CAGR {fmt_pct(b['cagr'])}, "
                         f"max drawdown {fmt_pct(b['max_drawdown'])}; buy-and-hold CAGR "
                         f"{fmt_pct(b['buy_and_hold_cagr'])}.")
        st.markdown("\n".join(lines))


def main() -> None:
    """Render the dashboard."""
    cfg, calendar = _setup()
    now = _now(cfg)
    preds = load_predictions(cfg)
    state = dashboard_state(cfg, calendar, now, preds)
    target = state.target

    st.title("MarketPredictor")
    st.warning(DISCLAIMER, icon="⚠️")
    st.markdown(f"### Prediction for: {target.target_date.strftime('%a %d %b %Y')}, "
                f"{day_label(target.target_date, now.date())}")
    shown = [p for p in state.latest.values() if p is not None]
    updated = max(p["created_at"] for p in shown).strftime("%d %b %Y, %H:%M IST") if shown else "—"
    st.caption(f"Last updated: {updated} · {state.market_note}")

    tabs = st.tabs([cfg["indices"][n]["name"] for n in cfg["indices"]])
    for tab, name in zip(tabs, cfg["indices"]):
        with tab:
            pred = state.latest[name]
            if pred is None:
                old = state.stale[name]
                if old is None:
                    st.info("No forecasts yet. Run `python scripts/daily_update.py`.")
                    continue
                st.error(f"No forecast for {target.target_date:%d %b} yet. Showing the last one, for "
                         f"{old['target_date']:%d %b %Y} ({day_label(old['target_date'], now.date())}).")
                pred = old
            show_index(name, cfg["indices"][name]["name"], pred, cfg)
            with st.expander("How good are these forecasts?"):
                quality_section(cfg, name)

    with st.expander("Track record: recent forecasts vs what happened"):
        store = MarketDataStore(cfg)
        bars = {n: store.get(cfg["indices"][n]["ticker"]) for n in cfg["indices"]}
        tr = track_record(preds, bars, cfg)
        if tr.empty:
            st.write("No completed sessions to compare yet.")
        else:
            st.dataframe(tr.head(30), width="stretch", hide_index=True)

    st.divider()
    st.caption(DISCLAIMER)


main()
