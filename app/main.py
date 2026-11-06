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

from app.data_access import (DISCLAIMER, dashboard_state, day_label, load_predictions,  # noqa: E402
                             model_quality, range_frame, track_record)
from app.plain import (BEST_GUESS, GLOSSARY, INDEX_ABOUT, PRICE_LABELS, RUN_LABELS,  # noqa: E402
                       direction_words, friendly_track_record, opening_outcomes, quality_lines,
                       range_lines, summary_sentences)
from data.calendar import TradingCalendar  # noqa: E402
from data.store import MarketDataStore  # noqa: E402
from settings import ist, load_config  # noqa: E402

# Colors (validated: ordinal blue pair for ranges; diverging blue/gray/red for the opening).
BAND_95, BAND_68, MEDIAN = "#86b6ef", "#2a78d6", "#ffffff"
OPEN_COLORS = {"Opens higher": "#2a78d6", "About the same": "#a3a29b", "Opens lower": "#e34948"}
REFERENCE = "#8a8985"
CAVEAT = ("Forecasts can be far off on days with big surprise news, such as elections, wars or sudden "
          "policy changes.")

st.set_page_config(page_title="MarketPredictor", page_icon="📈", layout="centered")


@st.cache_resource
def _setup():
    cfg = load_config(os.environ.get("MARKETPREDICTOR_CONFIG"))
    return cfg, TradingCalendar.from_config(cfg)


def _now(cfg) -> datetime:
    override = os.environ.get("MARKETPREDICTOR_NOW")
    return datetime.fromisoformat(override) if override else datetime.now(ist(cfg))


def opening_chart(rows: list[tuple[str, float]]) -> alt.Chart:
    """One bar split into the chances of opening higher / about the same / lower."""
    df = pd.DataFrame({"outcome": list(OPEN_COLORS), "detail": [r[0] for r in rows],
                       "p": [r[1] for r in rows], "order": range(3)})
    return alt.Chart(df).mark_bar(height=28, cornerRadius=4).encode(
        x=alt.X("sum(p):Q", stack="normalize", axis=None),
        order=alt.Order("order:Q"),
        color=alt.Color("outcome:N", scale=alt.Scale(domain=list(OPEN_COLORS), range=list(OPEN_COLORS.values())),
                        legend=None),
        tooltip=[alt.Tooltip("detail:N", title="Outcome"), alt.Tooltip("p:Q", title="Chance", format=".0%")],
    ).properties(height=36)


def range_chart(rf: pd.DataFrame, prev_close: float) -> alt.Chart:
    """Likely range (dark), wider range (light), best guess (white tick), yesterday's close (dashed)."""
    df = rf.assign(label=rf["key"].map(PRICE_LABELS))
    order = [PRICE_LABELS[k] for k in ("open", "high", "low")]
    y = alt.Y("label:N", sort=order, title=None, axis=alt.Axis(labelLimit=200))
    tip = [alt.Tooltip("label:N", title="Price"), alt.Tooltip("med:Q", title=BEST_GUESS, format=",.0f"),
           alt.Tooltip("lo68:Q", title="Likely: from", format=",.0f"), alt.Tooltip("hi68:Q", title="Likely: to", format=",.0f"),
           alt.Tooltip("lo95:Q", title="Wider: from", format=",.0f"), alt.Tooltip("hi95:Q", title="Wider: to", format=",.0f")]
    base = alt.Chart(df).encode(y=y, tooltip=tip)
    wide = base.mark_bar(color=BAND_95, height=14, cornerRadius=4).encode(
        x=alt.X("lo95:Q", title="Index level", scale=alt.Scale(zero=False), axis=alt.Axis(format=",.0f", grid=False)),
        x2="hi95:Q")
    likely = base.mark_bar(color=BAND_68, height=14, cornerRadius=4).encode(x="lo68:Q", x2="hi68:Q")
    best = base.mark_tick(color=MEDIAN, thickness=2, size=14).encode(x="med:Q")
    rule = alt.Chart(pd.DataFrame({"prev_close": [prev_close]})).mark_rule(
        color=REFERENCE, strokeDash=[4, 4], strokeWidth=1.5).encode(
        x="prev_close:Q", tooltip=[alt.Tooltip("prev_close:Q", title="Yesterday's close", format=",.0f")])
    return (wide + likely + best + rule).properties(height=150)


def show_index(name: str, pred: pd.Series, cfg) -> None:
    """Forecast panel for one index, in plain language."""
    flat = float(cfg["prediction"]["gap_threshold"])
    prev_close = float(pred["prev_close"])
    st.caption(INDEX_ABOUT.get(name, ""))
    if not bool(pred.get("data_refresh_ok", True)):
        st.warning("Some market data couldn't be refreshed for this forecast, so slightly older data was used.",
                   icon="⚠️")

    if (lines := summary_sentences(pred, flat)):
        st.info("**In short:** " + " ".join(lines), icon="💡")

    st.subheader("How will the market open?")
    if pd.notna(pred.get("p_gap_up")):
        headline, rows = opening_outcomes(pred, flat)
        st.markdown(headline)
        st.altair_chart(opening_chart(rows), width="stretch")
        st.markdown("  \n".join(f"{icon} {label}: **{p:.0%}**"
                                 for icon, (label, p) in zip(("🟦", "⬜", "🟥"), rows)))
        st.caption(f"Compared with yesterday's close of {prev_close:,.0f}.")
    else:
        st.info("No opening forecast available yet.")

    st.subheader("How far could it move today?")
    rf = range_frame(pred)
    if rf.empty:
        st.info("No price-range forecast available yet.")
    else:
        rf["key"] = rf["target"].str.lower()
        st.altair_chart(range_chart(rf, prev_close), width="stretch")
        st.caption("Dark blue: likely range (2 out of 3 days) · light blue: wider range (19 out of 20 days) · "
                   "white line: best guess · dashed line: yesterday's close.")
        st.markdown("\n".join(f"- {line}" for line in range_lines(rf)))
        if (rf["source"] == "vix_baseline").any():
            st.caption("\\* For these rows we show a simpler estimate based on India VIX (a measure of how "
                       "nervous the market is), because it did better in testing.")

    st.subheader("Will it end the day higher or lower?")
    p_up = float(pred["p_up"])
    lean, note = direction_words(p_up, bool(pred.get("model_beats_baseline", False)))
    st.metric("Chance of closing higher than yesterday", f"{p_up:.0%}")
    st.markdown(lean)
    if bool(pred.get("model_beats_baseline", False)):
        st.caption(note)
    else:
        st.warning(note, icon="⚠️")

    st.caption(CAVEAT)
    with st.expander("Technical details"):
        st.markdown(
            f"- Forecast type: {RUN_LABELS.get(pred['run'], pred['run'])}\n"
            f"- Based on the close of {pd.Timestamp(pred['prev_session']):%d %b %Y}: {prev_close:,.2f}\n"
            f"- Data used up to: {pd.Timestamp(pred['cutoff']):%d %b %Y, %H:%M IST}\n"
            f"- Models last trained on data up to: {pred.get('model_trained_through', '—')}")


def quality_section(cfg, name: str) -> None:
    """How the forecasts did in past testing, in everyday terms."""
    shown = False
    for run in ("morning", "evening"):
        q = model_quality(cfg, name, run)
        if not q:
            continue
        shown = True
        st.markdown(f"**Forecast {RUN_LABELS[run][0].lower()}{RUN_LABELS[run][1:]}**")
        st.markdown("\n".join(f"- {line}" for line in quality_lines(q)))
    if not shown:
        st.write("No test results available yet.")


def main() -> None:
    """Render the dashboard."""
    cfg, calendar = _setup()
    now = _now(cfg)
    preds = load_predictions(cfg)
    state = dashboard_state(cfg, calendar, now, preds)
    target = state.target

    st.title("MarketPredictor")
    st.caption("A daily outlook for India's two main stock market indices.")
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
                    st.info("No forecasts yet. They appear after the next scheduled update.")
                    continue
                st.error(f"The forecast for {target.target_date:%d %b} isn't ready yet. Showing the last one, "
                         f"for {old['target_date']:%d %b %Y} ({day_label(old['target_date'], now.date())}).")
                pred = old
            show_index(name, pred, cfg)
            with st.expander("How accurate has this been?"):
                quality_section(cfg, name)

    with st.expander("Recent forecasts vs what actually happened"):
        store = MarketDataStore(cfg)
        bars = {n: store.get(cfg["indices"][n]["ticker"]) for n in cfg["indices"]}
        tr = track_record(preds, bars, cfg)
        if tr.empty:
            st.write("No completed trading days to compare yet.")
        else:
            names = {n: cfg["indices"][n]["name"] for n in cfg["indices"]}
            st.dataframe(friendly_track_record(tr.head(30), names), width="stretch", hide_index=True)

    with st.expander("What do these words mean?"):
        st.markdown("\n".join(f"- **{term}:** {meaning}" for term, meaning in GLOSSARY))

    st.divider()
    st.caption(DISCLAIMER)


main()
