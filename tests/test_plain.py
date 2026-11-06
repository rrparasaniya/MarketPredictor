"""Plain-language wording rules for the dashboard."""

import pandas as pd
import pytest

from app.plain import (direction_words, friendly_track_record, move_phrase, opening_outcomes,
                       quality_lines, skill_words, summary_sentences)


def pred(**kw):
    base = dict(prev_close=24536.6, open_med=24582.0, high_med=24669.0, low_med=24455.0,
                p_gap_up=0.47, p_gap_flat=0.38, p_gap_down=0.15)
    return pd.Series({**base, **kw})


@pytest.mark.parametrize("level,phrase", [(24582, "near yesterday's level"), (24600, "a little higher"),
                                          (24700, "higher"), (24900, "sharply higher"),
                                          (24450, "a little lower"), (24300, "lower")])
def test_move_phrase(level, phrase):
    assert move_phrase(level, 24536.6, 0.002) == phrase


def test_summary_mentions_points_and_range():
    text = " ".join(summary_sentences(pred(), 0.002))
    assert "near yesterday's level" in text and "at about **24,582**" in text and "45 points above" in text
    assert "a little higher" in " ".join(summary_sentences(pred(open_med=24640.0), 0.002))
    assert "between **24,455** and **24,669**" in text


def test_opening_outcomes_headline_and_point_threshold():
    headline, rows = opening_outcomes(pred(), 0.002)
    assert "opens **higher** (47% chance)" in headline
    assert rows[0][0].startswith("Opens higher (more than ~49 points up)")
    close, _ = opening_outcomes(pred(p_gap_up=0.40, p_gap_flat=0.38, p_gap_down=0.22), 0.002)
    assert "No clear expectation" in close


def test_direction_words_reliability():
    lean, note = direction_words(0.69, reliable=False)
    assert "closing **higher**" in lean and "coin toss" in note
    lean, note = direction_words(0.50, reliable=True)
    assert lean == "No clear lean either way." and "not** a buy or sell signal" in note
    assert "**lower**" in direction_words(0.30, True)[0]


def test_skill_words():
    assert skill_words(0.78) == "much better than chance"
    assert skill_words(0.60) == "somewhat better than chance"
    assert skill_words(0.51) == "about the same as chance"


def test_quality_lines_everyday_terms():
    q = {"direction": {"period": "2011-06-27 to 2026-11-03", "accuracy": 0.591, "baseline_accuracy": 0.522,
                       "beats_baseline": True},
         "gap": {"up": {"roc_auc": 0.75}, "down": {"roc_auc": 0.78}},
         "range": {"open": {"coverage_68": 0.67, "coverage_95": 0.95},
                   "high": {"coverage_68": 0.68, "coverage_95": 0.95}},
         "backtest": {"cagr": -0.119, "buy_and_hold_cagr": 0.103}}
    text = " ".join(quality_lines(q))
    assert "**59 of 100** days" in text and "since 2011" in text
    assert "better than simple guessing rules (52 of 100)" in text
    assert "much better than chance" in text
    assert "**lost money**" in text and "-12% a year" in text and "+10% a year" in text
    assert "ROC" not in text and "CAGR" not in text


def test_friendly_track_record():
    tr = pd.DataFrame([{"index": "nifty", "session": pd.Timestamp("2026-11-05").date(), "p_up": 0.63,
                        "actual": "up", "close_change_pct": 2.4, "direction_correct": True,
                        "gap_call": "up", "gap_actual": "up", "open_in_68": False, "high_in_68": False,
                        "low_in_68": False}])
    out = friendly_track_record(tr, {"nifty": "NIFTY 50"})
    row = out.iloc[0]
    assert row["Date"] == "05 Nov" and row["Index"] == "NIFTY 50"
    assert row["Forecast"] == "Higher (63%)" and row["Actual"] == "Higher (+2.4%)" and row["Right?"] == "✅"
    assert row["Opening right?"] == "✅" and row["In likely range"] == "0 of 3"


def test_range_lines_phone_friendly():
    from app.plain import range_lines
    rf = pd.DataFrame([{"key": "open", "source": "model", "med": 24069.0, "lo68": 23989.0, "hi68": 24119.0,
                        "lo95": 23746.0, "hi95": 24312.0},
                       {"key": "low", "source": "vix_baseline", "med": 23947.0, "lo68": 23776.0, "hi68": 24066.0,
                        "lo95": 23490.0, "hi95": 24190.0}])
    lines = range_lines(rf)
    assert lines[0] == ("**Opening price:** best guess **24,069** · likely 23,989 – 24,119 · "
                        "wider 23,746 – 24,312")
    assert lines[1].startswith("**Lowest price of the day \\*:**")
