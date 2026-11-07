## Backtest: sensex (evening run)

Out-of-sample 2011-06-24 to 2026-11-06 (3772 sessions). Trades enter at the target session's open and exit at its close, on index prices as a stand-in for futures. Net of brokerage, STT, exchange charges, SEBI fee, GST, stamp duty and slippage. Sharpe uses a 6.5% risk-free rate; 'idle cash 0' assumes unused capital earns nothing (conservative), 'idle cash rf' assumes it earns the risk-free rate.

| strategy | trades | exposure | hit rate | avg trade bps | total return | CAGR | ann vol | Sharpe (idle cash 0) | Sharpe (idle cash rf) | max DD |
|---|---|---|---|---|---|---|---|---|---|---|
| model | 1440 | 38.2% | 45.1% | -9.8 | -77.0% | -9.4% | 8.6% | -1.85 | -1.10 | -78.7% |
| model_gross | 1440 | 38.2% | 48.1% | -4.6 | -50.9% | -4.6% | 8.6% | -1.27 | -0.51 | -57.7% |
| baseline_always_up | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| baseline_previous_day | 718 | 19.0% | 43.6% | -8.7 | -47.5% | -4.2% | 4.7% | -2.30 | -0.90 | -50.3% |
| baseline_ema_20_50 | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| always_long_intraday | 3772 | 100.0% | 42.9% | -13.8 | -99.5% | -30.0% | 13.7% | -3.01 | -2.54 | -99.6% |
| buy_and_hold | — | — | — | — | 354.8% | 10.6% | 16.4% | 0.30 | 0.70 | -38.1% |
| model_prev_close_entry ⚠ | 1440 | 38.2% | 55.0% | 7.0 | 152.1% | 6.4% | 10.3% | 0.02 | 0.65 | -32.7% |

- `model`: p_model_lightgbm: long >= 0.55, short <= 0.45
- `model_gross`: same trades, no costs
- `always_long_intraday`: long every session open -> close
- `buy_and_hold`: index close to close, no costs
- `model_prev_close_entry`: NOT EXECUTABLE: enters at the previous close, before the forecast exists. Shows how much of the edge is the overnight gap.

### Threshold sensitivity (model, net)

| long ≥ / short ≤ | trades | hit rate | avg trade bps | CAGR | Sharpe (idle cash 0) | max DD |
|---|---|---|---|---|---|---|
| 0.50 / 0.50 | 3772 | 44.7% | -10.5 | -24.0% | -2.40 | -98.8% |
| 0.52 / 0.48 | 2874 | 44.5% | -11.3 | -20.0% | -2.35 | -97.2% |
| 0.55 / 0.45 | 1440 | 45.1% | -9.8 | -9.4% | -1.85 | -78.7% |
| 0.60 / 0.40 | 228 | 42.5% | -13.0 | -2.0% | -2.69 | -28.9% |

### Model trades by regime and event

| subset | sessions | trades | hit rate | avg net bps | avg gross bps |
|---|---|---|---|---|---|
| vix_low | 711 | 305 | 46.2% | -5.9 | -0.8 |
| vix_normal | 2248 | 836 | 44.5% | -12.2 | -6.9 |
| vix_high | 813 | 299 | 45.5% | -7.3 | -1.7 |
| is_expiry | 324 | 135 | 45.9% | -4.9 | 0.2 |
| not_is_expiry | 3448 | 1305 | 45.0% | -10.3 | -5.1 |
| is_monthly_expiry | 185 | 65 | 43.1% | -7.3 | -2.1 |
| not_is_monthly_expiry | 3587 | 1375 | 45.2% | -9.9 | -4.7 |
| is_rbi_policy | 25 | 13 | 53.8% | 10.9 | 15.9 |
| not_is_rbi_policy | 959 | 484 | 46.3% | -7.2 | -2.2 |
| is_union_budget | 16 | 6 | 66.7% | 85.4 | 90.7 |
| not_is_union_budget | 3756 | 1434 | 45.0% | -10.2 | -5.0 |
| is_election_results | 3 | 3 | 0.0% | -275.3 | -270.1 |
| not_is_election_results | 3769 | 1437 | 45.2% | -9.3 | -4.0 |

### Return by year

| year | model | model_gross | always_long_intraday | buy_and_hold |
|---|---|---|---|---|
| 2011 | 1.7% | 3.8% | -28.9% | -12.8% |
| 2012 | -5.2% | 0.6% | -17.5% | 25.7% |
| 2013 | -9.0% | -5.6% | -30.5% | 9.0% |
| 2014 | -5.0% | 0.1% | -21.9% | 29.9% |
| 2015 | -13.7% | -8.9% | -45.5% | -5.0% |
| 2016 | -0.6% | 1.6% | -35.6% | 1.9% |
| 2017 | -4.6% | -2.6% | -26.6% | 27.9% |
| 2018 | -30.8% | -24.8% | -37.3% | 5.9% |
| 2019 | -13.0% | -8.6% | -39.3% | 14.4% |
| 2020 | -7.5% | -6.0% | -42.0% | 15.8% |
| 2021 | -13.4% | -6.9% | -35.3% | 22.0% |
| 2022 | 2.9% | 9.7% | -9.9% | 4.4% |
| 2023 | -6.5% | 0.4% | -15.7% | 18.7% |
| 2024 | -24.3% | -19.1% | -25.7% | 7.7% |
| 2025 | -2.7% | 1.8% | -10.5% | 9.0% |
| 2026 | -1.5% | 1.1% | -19.5% | -4.9% |

### Warnings

- The model strategy loses money after costs over the test period.
