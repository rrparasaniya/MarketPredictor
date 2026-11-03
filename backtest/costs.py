"""Indian index-futures transaction costs (all rates from config)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CostModel:
    """Per-round-trip costs for one buy and one sell of index futures.

    Percent fields are in percent of traded value (0.02 means 0.02%).
    """

    brokerage_per_order: float
    stt_sell_pct: float
    exchange_txn_pct: float
    sebi_fee_pct: float
    stamp_duty_buy_pct: float
    gst_pct: float
    slippage_pct_per_side: float

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> CostModel:
        """Build from ``cfg['backtest']['costs']``."""
        return cls(**{k: float(v) for k, v in cfg["backtest"]["costs"].items()})

    def fill_prices(self, entry: np.ndarray, exit_: np.ndarray, side: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Entry/exit prices after slippage (buys fill higher, sells lower).

        ``side`` is +1 (long: buy at entry, sell at exit) or -1 (short: the reverse).
        """
        s = self.slippage_pct_per_side / 100
        return entry * (1 + side * s), exit_ * (1 - side * s)

    def charges(self, buy_value: np.ndarray, sell_value: np.ndarray) -> dict[str, np.ndarray]:
        """Statutory and broker charges in rupees for one buy and one sell."""
        turnover = buy_value + sell_value
        brokerage = np.full_like(turnover, 2 * self.brokerage_per_order, dtype=float)
        exchange = turnover * self.exchange_txn_pct / 100
        sebi = turnover * self.sebi_fee_pct / 100
        out = {
            "brokerage": brokerage,
            "stt": sell_value * self.stt_sell_pct / 100,
            "exchange": exchange,
            "sebi": sebi,
            "stamp_duty": buy_value * self.stamp_duty_buy_pct / 100,
            "gst": (brokerage + exchange + sebi) * self.gst_pct / 100,
        }
        out["total"] = sum(out.values())
        return out
