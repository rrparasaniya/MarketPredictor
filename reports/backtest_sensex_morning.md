## Backtest: sensex (morning run)

Out-of-sample 2011-06-24 to 2026-11-13 (3776 sessions). Trades enter at the target session's open and exit at its close, on index prices as a stand-in for futures. Net of brokerage, STT, exchange charges, SEBI fee, GST, stamp duty and slippage. Sharpe uses a 6.5% risk-free rate; 'idle cash 0' assumes unused capital earns nothing (conservative), 'idle cash rf' assumes it earns the risk-free rate.

| strategy | trades | exposure | hit rate | avg trade bps | total return | CAGR | ann vol | Sharpe (idle cash 0) | Sharpe (idle cash rf) | max DD |
|---|---|---|---|---|---|---|---|---|---|---|
| model | 2663 | 70.5% | 46.9% | -5.6 | -79.3% | -10.0% | 11.3% | -1.44 | -0.87 | -80.2% |
| model_gross | 2663 | 70.5% | 50.4% | -0.3 | -15.9% | -1.1% | 11.3% | -0.62 | -0.04 | -41.4% |
| baseline_always_up | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| baseline_previous_day | 722 | 19.1% | 43.5% | -8.8 | -48.0% | -4.3% | 4.7% | -2.31 | -0.91 | -50.3% |
| baseline_ema_20_50 | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| always_long_intraday | 3776 | 100.0% | 42.9% | -13.8 | -99.5% | -30.0% | 13.7% | -3.01 | -2.54 | -99.6% |
| buy_and_hold | — | — | — | — | 358.0% | 10.7% | 16.4% | 0.31 | 0.70 | -38.1% |
| model_prev_close_entry ⚠ | 2663 | 70.5% | 60.5% | 23.4 | 44122.4% | 50.2% | 13.7% | 2.56 | 3.03 | -16.5% |

- `model`: p_model_lightgbm: long >= 0.55, short <= 0.45
- `model_gross`: same trades, no costs
- `always_long_intraday`: long every session open -> close
- `buy_and_hold`: index close to close, no costs
- `model_prev_close_entry`: NOT EXECUTABLE: enters at the previous close, before the forecast exists. Shows how much of the edge is the overnight gap.

### Threshold sensitivity (model, net)

| long ≥ / short ≤ | trades | hit rate | avg trade bps | CAGR | Sharpe (idle cash 0) | max DD |
|---|---|---|---|---|---|---|
| 0.50 / 0.50 | 3776 | 46.5% | -6.2 | -15.3% | -1.61 | -92.1% |
| 0.52 / 0.48 | 3302 | 46.8% | -5.4 | -12.0% | -1.43 | -86.1% |
| 0.55 / 0.45 | 2663 | 46.9% | -5.6 | -10.0% | -1.44 | -80.2% |
| 0.60 / 0.40 | 1694 | 46.3% | -6.1 | -7.1% | -1.55 | -69.3% |

### Model trades by regime and event

| subset | sessions | trades | hit rate | avg net bps | avg gross bps |
|---|---|---|---|---|---|
| vix_low | 711 | 556 | 48.4% | -3.2 | 1.8 |
| vix_normal | 2252 | 1552 | 45.4% | -6.8 | -1.5 |
| vix_high | 813 | 555 | 49.5% | -4.5 | 1.0 |
| is_expiry | 325 | 240 | 47.5% | -3.7 | 1.4 |
| not_is_expiry | 3451 | 2423 | 46.8% | -5.7 | -0.5 |
| is_monthly_expiry | 185 | 121 | 46.3% | -2.2 | 3.1 |
| not_is_monthly_expiry | 3591 | 2542 | 46.9% | -5.7 | -0.4 |
| is_rbi_policy | 25 | 21 | 66.7% | -5.7 | -0.7 |
| not_is_rbi_policy | 959 | 811 | 46.4% | -7.7 | -2.7 |
| is_union_budget | 16 | 12 | 33.3% | -66.1 | -60.8 |
| not_is_union_budget | 3760 | 2651 | 46.9% | -5.3 | -0.0 |
| is_election_results | 3 | 1 | 0.0% | -556.2 | -551.4 |
| not_is_election_results | 3773 | 2662 | 46.9% | -5.3 | -0.1 |

### Return by year

| year | model | model_gross | always_long_intraday | buy_and_hold |
|---|---|---|---|---|
| 2011 | 1.3% | 6.1% | -28.9% | -12.8% |
| 2012 | -10.2% | -3.4% | -17.5% | 25.7% |
| 2013 | -19.1% | -14.2% | -30.5% | 9.0% |
| 2014 | 8.0% | 14.5% | -21.9% | 29.9% |
| 2015 | -4.3% | 6.3% | -45.5% | -5.0% |
| 2016 | 6.4% | 16.8% | -35.6% | 1.9% |
| 2017 | 1.6% | 10.3% | -26.6% | 27.9% |
| 2018 | -26.2% | -18.1% | -37.3% | 5.9% |
| 2019 | -17.2% | -8.9% | -39.3% | 14.4% |
| 2020 | 10.9% | 22.4% | -42.0% | 15.8% |
| 2021 | -18.4% | -9.8% | -35.3% | 22.0% |
| 2022 | -14.0% | -4.5% | -9.9% | 4.4% |
| 2023 | -0.3% | 10.7% | -15.7% | 18.7% |
| 2024 | -21.5% | -13.0% | -25.7% | 7.7% |
| 2025 | -22.7% | -14.6% | -10.5% | 9.0% |
| 2026 | -12.4% | -5.7% | -20.3% | -4.3% |

### Warnings

- The model strategy loses money after costs over the test period.
