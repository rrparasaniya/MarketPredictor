"""Direction baselines the ML model must be compared against.

Each baseline turns a simple rule into a probability by measuring, on the training
window only, how often the market went up when the rule fired vs. when it didn't.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class _RuleBaseline:
    """P(up | rule state), estimated on the training fold with Laplace smoothing."""

    name = "rule"

    def signal(self, X: pd.DataFrame) -> pd.Series:
        """True/False per row, or NaN when the rule can't be evaluated."""
        raise NotImplementedError

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "_RuleBaseline":
        y = np.asarray(y, dtype=float)
        s = self.signal(X).to_numpy()
        self.base_rate_ = (y.sum() + 1) / (len(y) + 2)
        self.rates_ = {}
        for state in (True, False):
            m = s == state
            self.rates_[state] = (y[m].sum() + 1) / (m.sum() + 2) if m.any() else self.base_rate_
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        s = self.signal(X).to_numpy()
        p = np.full(len(X), self.base_rate_)
        p[s == True] = self.rates_[True]   # noqa: E712 (object array with NaN)
        p[s == False] = self.rates_[False]  # noqa: E712
        return np.column_stack([1 - p, p])


class AlwaysUp(_RuleBaseline):
    """Always predicts up, with P(up) = the training up-rate."""

    name = "always_up"

    def signal(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(True, index=X.index, dtype=object)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        # Hard rule: always "up". The probability is the training up-rate, floored at 0.5
        # so the 0.5 decision threshold always says up.
        p = np.full(len(X), max(self.rates_[True], 0.5))
        return np.column_stack([1 - p, p])


class PreviousDay(_RuleBaseline):
    """Predicts the same direction as the last completed session."""

    name = "previous_day"

    def __init__(self, threshold: float = 0.0) -> None:
        self.threshold = threshold

    def signal(self, X: pd.DataFrame) -> pd.Series:
        r = X["idx_ret_1"]
        return (r > np.log1p(self.threshold)).astype(object).where(r.notna())


class EmaCrossover(_RuleBaseline):
    """Up when EMA(20) is above EMA(50) as of the last completed session."""

    name = "ema_20_50"

    def signal(self, X: pd.DataFrame) -> pd.Series:
        g = X["idx_ema20_50"]
        return (g > 0).astype(object).where(g.notna())


class BaseRate(_RuleBaseline):
    """P(class 1) = the training base rate, for every row."""

    name = "base_rate"

    def signal(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(np.nan, index=X.index, dtype=object)


class ThresholdRule(_RuleBaseline):
    """Rule ``column > threshold`` (or ``<`` with ``below=True``), as a probability."""

    def __init__(self, name: str, column: str, threshold: float = 0.0, below: bool = False) -> None:
        self.name, self.column, self.threshold, self.below = name, column, threshold, below

    def signal(self, X: pd.DataFrame) -> pd.Series:
        v = X[self.column] if self.column in X else pd.Series(np.nan, index=X.index)
        fired = v < self.threshold if self.below else v > self.threshold
        return fired.astype(object).where(v.notna())


def gap_baselines(direction: str, gap_threshold: float) -> dict[str, object]:
    """Baselines for P(gap up) (``direction="up"``) or P(gap down) (``"down"``)."""
    down = direction == "down"
    thr = -np.log1p(gap_threshold) if down else np.log1p(gap_threshold)
    return {
        "base_rate": BaseRate,
        "previous_gap": lambda: ThresholdRule("previous_gap", "idx_gap", thr, below=down),
        "us_overnight": lambda: ThresholdRule("us_overnight", "gspc_ret_1", 0.0, below=down),
    }


def all_baselines(threshold: float = 0.0) -> dict[str, type | object]:
    """Factories for every direction baseline, keyed by name."""
    return {
        AlwaysUp.name: AlwaysUp,
        PreviousDay.name: lambda: PreviousDay(threshold),
        EmaCrossover.name: EmaCrossover,
    }
