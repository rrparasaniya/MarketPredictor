## Backtest: nifty (evening run)

Out-of-sample 2011-06-27 to 2026-11-27 (3780 sessions). Trades enter at the target session's open and exit at its close, on index prices as a stand-in for futures. Net of brokerage, STT, exchange charges, SEBI fee, GST, stamp duty and slippage. Sharpe uses a 6.5% risk-free rate; 'idle cash 0' assumes unused capital earns nothing (conservative), 'idle cash rf' assumes it earns the risk-free rate.

| strategy | trades | exposure | hit rate | avg trade bps | total return | CAGR | ann vol | Sharpe (idle cash 0) | Sharpe (idle cash rf) | max DD |
|---|---|---|---|---|---|---|---|---|---|---|
| model | 1508 | 39.9% | 45.3% | -9.7 | -78.1% | -9.6% | 9.0% | -1.79 | -1.07 | -78.8% |
| model_gross | 1508 | 39.9% | 48.9% | -4.5 | -52.1% | -4.8% | 9.0% | -1.22 | -0.50 | -55.6% |
| baseline_always_up | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| baseline_previous_day | 699 | 18.5% | 43.9% | -8.1 | -44.1% | -3.8% | 4.4% | -2.31 | -0.85 | -47.7% |
| baseline_ema_20_50 | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| always_long_intraday | 3780 | 100.0% | 43.8% | -11.1 | -98.7% | -25.2% | 13.5% | -2.57 | -2.09 | -98.8% |
| buy_and_hold | — | — | — | — | 365.7% | 10.8% | 16.3% | 0.31 | 0.71 | -38.4% |
| model_prev_close_entry ⚠ | 1508 | 39.9% | 54.5% | 3.7 | 59.5% | 3.2% | 11.0% | -0.25 | 0.34 | -36.5% |

- `model`: p_model_lightgbm: long >= 0.55, short <= 0.45
- `model_gross`: same trades, no costs
- `always_long_intraday`: long every session open -> close
- `buy_and_hold`: index close to close, no costs
- `model_prev_close_entry`: NOT EXECUTABLE: enters at the previous close, before the forecast exists. Shows how much of the edge is the overnight gap.

### Threshold sensitivity (model, net)

| long ≥ / short ≤ | trades | hit rate | avg trade bps | CAGR | Sharpe (idle cash 0) | max DD |
|---|---|---|---|---|---|---|
| 0.50 / 0.50 | 3780 | 45.2% | -9.0 | -21.0% | -2.17 | -97.6% |
| 0.52 / 0.48 | 2918 | 44.9% | -9.1 | -16.8% | -2.02 | -94.7% |
| 0.55 / 0.45 | 1508 | 45.3% | -9.7 | -9.6% | -1.79 | -78.8% |
| 0.60 / 0.40 | 368 | 38.3% | -11.4 | -2.8% | -2.37 | -37.8% |

### Model trades by regime and event

| subset | sessions | trades | hit rate | avg net bps | avg gross bps |
|---|---|---|---|---|---|
| vix_low | 712 | 282 | 43.3% | -6.8 | -1.8 |
| vix_normal | 2257 | 878 | 44.1% | -11.3 | -6.2 |
| vix_high | 811 | 348 | 50.0% | -7.8 | -2.4 |
| is_expiry | 499 | 226 | 46.9% | -9.4 | -4.3 |
| not_is_expiry | 3281 | 1282 | 45.0% | -9.7 | -4.5 |
| is_monthly_expiry | 186 | 74 | 54.1% | -5.8 | -0.6 |
| not_is_monthly_expiry | 3594 | 1434 | 44.8% | -9.9 | -4.7 |
| is_rbi_policy | 25 | 13 | 61.5% | 18.0 | 23.0 |
| not_is_rbi_policy | 961 | 501 | 45.5% | -6.9 | -2.0 |
| is_union_budget | 17 | 8 | 50.0% | 27.9 | 33.1 |
| not_is_union_budget | 3763 | 1500 | 45.3% | -9.9 | -4.7 |
| is_election_results | 3 | 2 | 0.0% | -386.9 | -382.0 |
| not_is_election_results | 3777 | 1506 | 45.4% | -9.2 | -4.0 |

### Return by year

| year | model | model_gross | always_long_intraday | buy_and_hold |
|---|---|---|---|---|
| 2011 | -3.6% | -1.5% | -28.0% | -15.5% |
| 2012 | -1.8% | 3.1% | -7.7% | 27.7% |
| 2013 | -8.2% | -2.6% | -25.7% | 6.8% |
| 2014 | 0.1% | 1.2% | -12.0% | 31.4% |
| 2015 | -15.3% | -9.4% | -37.5% | -4.1% |
| 2016 | -6.2% | -4.4% | -29.7% | 3.0% |
| 2017 | -1.0% | 1.0% | -24.7% | 28.6% |
| 2018 | -17.7% | -12.9% | -27.2% | 3.2% |
| 2019 | -16.6% | -10.5% | -30.6% | 12.0% |
| 2020 | -8.3% | -6.9% | -35.0% | 14.9% |
| 2021 | -24.0% | -16.7% | -30.8% | 24.1% |
| 2022 | -1.0% | 5.6% | -14.2% | 4.3% |
| 2023 | -4.0% | 2.4% | -22.2% | 20.0% |
| 2024 | -19.8% | -14.1% | -23.9% | 8.4% |
| 2025 | -6.3% | -0.9% | -10.2% | 10.4% |
| 2026 | -6.2% | -1.8% | -13.5% | -2.0% |

### Warnings

- The model strategy loses money after costs over the test period.
