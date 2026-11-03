"""Walk-forward (time-ordered) validation. Never shuffles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

import numpy as np
import pandas as pd


class ProbabilisticClassifier(Protocol):
    """Anything with sklearn-style ``fit`` and ``predict_proba``."""

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Any: ...

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: ...


@dataclass(frozen=True)
class Fold:
    """One walk-forward step: train on ``train_idx``, then predict ``test_idx``."""

    number: int
    train_idx: np.ndarray
    test_idx: np.ndarray


def walk_forward_splits(n: int, min_train: int, test_size: int, embargo: int = 0,
                        max_train: int | None = None) -> list[Fold]:
    """Expanding (or rolling, with ``max_train``) walk-forward folds over ``n`` rows.

    Every training row comes strictly before every test row, with ``embargo`` rows
    left out in between. Rows must already be sorted by time.
    """
    if min_train <= embargo or test_size <= 0:
        raise ValueError("need min_train > embargo and test_size > 0")
    folds = []
    start = min_train
    while start < n:
        train_end = start - embargo
        train_start = 0 if max_train is None else max(0, train_end - max_train)
        folds.append(Fold(len(folds), np.arange(train_start, train_end),
                          np.arange(start, min(start + test_size, n))))
        start += test_size
    return folds


def splits_from_config(n: int, cfg: dict[str, Any]) -> list[Fold]:
    """Walk-forward folds using ``cfg['validation']``."""
    v = cfg["validation"]
    return walk_forward_splits(n, int(v["min_train_sessions"]), int(v["test_sessions"]),
                               int(v.get("embargo_sessions", 0)), v.get("max_train_sessions"))


def walk_forward_predict(X: pd.DataFrame, y: pd.Series, make_model: Callable[[], ProbabilisticClassifier],
                         folds: list[Fold]) -> pd.DataFrame:
    """Out-of-sample P(class 1) for every test row, refitting a fresh model per fold.

    Returns:
        A frame indexed like the test rows of ``X`` with columns ``p`` and ``fold``.
    """
    if not X.index.is_monotonic_increasing:
        raise ValueError("rows must be sorted by time")
    out = []
    for fold in folds:
        model = make_model()
        model.fit(X.iloc[fold.train_idx], y.iloc[fold.train_idx])
        p = model.predict_proba(X.iloc[fold.test_idx])[:, 1]
        out.append(pd.DataFrame({"p": p, "fold": fold.number}, index=X.index[fold.test_idx]))
    if not out:
        return pd.DataFrame(columns=["p", "fold"], index=X.index[:0])
    return pd.concat(out)
