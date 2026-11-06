"""Plain-language wording for the dashboard, for readers with no trading background.

Pure functions (no Streamlit) so the wording rules can be unit-tested.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

# Row labels and column names used everywhere the ranges appear.
PRICE_LABELS = {"open": "Opening price", "high": "Highest price of the day", "low": "Lowest price of the day"}
BEST_GUESS = "Best guess"
LIKELY = "Likely range (2 out of 3 days)"
WIDER = "Wider range (19 out of 20 days)"

INDEX_ABOUT = {
    "nifty": "Tracks India's 50 largest companies listed on the National Stock Exchange (NSE).",
    "sensex": "Tracks 30 large, well-established companies listed on the Bombay Stock Exchange (BSE).",
}

RUN_LABELS = {"morning": "Made before the market opens (around 8:30 AM)",
              "evening": "Made the evening before"}

GLOSSARY = [
    ("Index", "A single number that tracks a group of big companies. When most of their share "
              "prices rise, the index rises."),
    ("Close / yesterday's close", "The index level when the market shut at 3:30 PM on the last "
                                  "trading day. Every forecast is measured against it."),
    ("Open", "The index level when the market starts trading at 9:15 AM."),
    ("Points", "The index's own units. 100 points on NIFTY 50 is about 0.4%."),
    ("Best guess", "The single most likely value."),
    ("Likely range", "Where the price should land on about 2 out of 3 days."),
    ("Wider range", "Where the price should land on about 19 out of 20 days. Outside it means a "
                    "very unusual day."),
    ("Chance (%)", "How often this kind of forecast came true in past testing. 50% is a coin toss."),
]


def _points(level: float, prev_close: float) -> str:
    diff = level - prev_close
    return f"{abs(diff):,.0f} points {'above' if diff >= 0 else 'below'}"


def move_phrase(level: float, prev_close: float, flat_threshold: float) -> str:
    """Describe a move from the previous close in words, e.g. "a little higher"."""
    chg = level / prev_close - 1
    if abs(chg) < flat_threshold:
        return "near yesterday's level"
    size = "a little " if abs(chg) < 0.005 else "" if abs(chg) < 0.01 else "sharply "
    return f"{size}{'higher' if chg > 0 else 'lower'}"


def summary_sentences(pred: pd.Series, flat_threshold: float) -> list[str]:
    """The "In short" box: expected open and the day's likely trading range."""
    pc = float(pred["prev_close"])
    out = []
    if pd.notna(pred.get("open_med")):
        o = float(pred["open_med"])
        out.append(f"Expected to open **{move_phrase(o, pc, flat_threshold)}**, at about **{o:,.0f}** "
                   f"({_points(o, pc)} yesterday's close of {pc:,.0f}).")
    if pd.notna(pred.get("low_med")) and pd.notna(pred.get("high_med")):
        out.append(f"During the day it will most likely trade between **{float(pred['low_med']):,.0f}** "
                   f"and **{float(pred['high_med']):,.0f}**.")
    return out


def opening_outcomes(pred: pd.Series, flat_threshold: float) -> tuple[str, list[tuple[str, float]]]:
    """Headline and (label, chance) rows for how the market is likely to open."""
    pc = float(pred["prev_close"])
    pts = pc * flat_threshold
    rows = [(f"Opens higher (more than ~{pts:,.0f} points up)", float(pred["p_gap_up"])),
            (f"Opens about the same (within ~{pts:,.0f} points)", float(pred["p_gap_flat"])),
            (f"Opens lower (more than ~{pts:,.0f} points down)", float(pred["p_gap_down"]))]
    names = ["higher", "about the same", "lower"]
    best = max(range(3), key=lambda i: rows[i][1])
    second = sorted((r[1] for r in rows), reverse=True)[1]
    if rows[best][1] - second < 0.05:
        headline = "No clear expectation for the opening: two outcomes are about equally likely."
    else:
        headline = f"Most likely the market opens **{names[best]}** ({rows[best][1]:.0%} chance)."
    return headline, rows


def direction_words(p_up: float, reliable: bool) -> tuple[str, str]:
    """(lean, reliability note) for the chance of closing higher than yesterday."""
    if p_up >= 0.65:
        lean = "Leans towards closing **higher** than yesterday."
    elif p_up >= 0.55:
        lean = "Slightly leans towards closing **higher** than yesterday."
    elif p_up > 0.45:
        lean = "No clear lean either way."
    elif p_up > 0.35:
        lean = "Slightly leans towards closing **lower** than yesterday."
    else:
        lean = "Leans towards closing **lower** than yesterday."
    if reliable:
        note = ("In past testing this forecast was right more often than simple guessing, but mostly "
                "because it reads overnight news from other markets. That news is usually already "
                "reflected in prices when the market opens, so it is **not** a buy or sell signal.")
    else:
        note = ("**Low reliability:** in past testing this forecast was no better than simple guessing. "
                "Treat it like a coin toss.")
    return lean, note


def skill_words(auc: float | None) -> str:
    """Translate a ROC-AUC score into words (0.5 = coin toss)."""
    if auc is None:
        return "not measured yet"
    if auc >= 0.70:
        return "much better than chance"
    if auc >= 0.55:
        return "somewhat better than chance"
    return "about the same as chance"


def _per100(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.0f}"


def quality_lines(q: dict[str, Any]) -> list[str]:
    """Past-performance summary for one forecast time, in everyday terms."""
    lines = []
    if (d := q.get("direction")):
        start = str(d["period"])[:4]
        verdict = "better than" if d["beats_baseline"] else "no better than"
        lines.append(f"**Higher or lower close:** right on **{_per100(d['accuracy'])} of 100** days in tests "
                     f"since {start}, {verdict} simple guessing rules "
                     f"({_per100(d['baseline_accuracy'])} of 100).")
    if (g := q.get("gap")):
        up, down = g.get("up", {}).get("roc_auc"), g.get("down", {}).get("roc_auc")
        best = max(a for a in (up, down) if a is not None) if (up or down) else None
        lines.append(f"**How it opens:** {skill_words(best)} at telling whether the market will open "
                     "higher or lower.")
    if (r := q.get("range")):
        cov68 = [v["coverage_68"] for v in r.values()]
        cov95 = [v["coverage_95"] for v in r.values()]
        lines.append(f"**Price ranges:** the likely range held on about **{_per100(sum(cov68) / len(cov68))} "
                     f"of 100** days (aim: 68) and the wider range on about "
                     f"**{_per100(sum(cov95) / len(cov95))} of 100** (aim: 95).")
    if (b := q.get("backtest")) and b.get("cagr") is not None:
        lines.append(f"**Trading on it:** buying or selling each day on the higher/lower forecast would have "
                     f"**lost money** after costs ({b['cagr'] * 100:+.0f}% a year), while simply holding the "
                     f"index made about {b['buy_and_hold_cagr'] * 100:+.0f}% a year."
                     if b["cagr"] < 0 else
                     f"**Trading on it:** about {b['cagr'] * 100:+.0f}% a year after costs, vs "
                     f"{b['buy_and_hold_cagr'] * 100:+.0f}% for simply holding the index.")
    return lines


def range_lines(rf: pd.DataFrame) -> list[str]:
    """One phone-friendly line per price (open / high / low) instead of a wide table."""
    out = []
    for _, r in rf.iterrows():
        star = " \\*" if r.get("source") == "vix_baseline" else ""
        out.append(f"**{PRICE_LABELS[r['key']]}{star}:** best guess **{r['med']:,.0f}** · "
                   f"likely {r['lo68']:,.0f} – {r['hi68']:,.0f} · wider {r['lo95']:,.0f} – {r['hi95']:,.0f}")
    return out


def friendly_track_record(tr: pd.DataFrame, index_names: dict[str, str]) -> pd.DataFrame:
    """Past forecasts vs reality with plain column names and ✅/❌ marks."""
    if tr.empty:
        return tr

    def mark(v: Any) -> str:
        return "—" if pd.isna(v) else ("✅" if bool(v) else "❌")

    out = pd.DataFrame({
        "Date": pd.to_datetime(tr["session"]).dt.strftime("%d %b"),
        "Index": tr["index"].map(index_names).fillna(tr["index"]),
        "Forecast": tr.apply(lambda r: f"{'Higher' if r['p_up'] >= 0.5 else 'Lower'} ({r['p_up']:.0%})", axis=1),
        "Actual": tr.apply(lambda r: f"{'Higher' if r['actual'] == 'up' else 'Lower'} "
                                     f"({r['close_change_pct']:+.1f}%)", axis=1),
        "Right?": tr["direction_correct"].map(mark),
    })
    if "gap_call" in tr:
        out["Opening right?"] = (tr["gap_call"] == tr["gap_actual"]).where(tr["gap_call"].notna()).map(mark)
    cols = [f"{k}_in_68" for k in ("open", "high", "low") if f"{k}_in_68" in tr]
    if cols:
        out["In likely range"] = tr[cols].apply(
            lambda r: f"{int(r.sum())} of {r.notna().sum()}" if r.notna().any() else "—", axis=1)
    return out
