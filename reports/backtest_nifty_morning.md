## Backtest: nifty (morning run)

Out-of-sample 2011-06-27 to 2026-11-13 (3771 sessions). Trades enter at the target session's open and exit at its close, on index prices as a stand-in for futures. Net of brokerage, STT, exchange charges, SEBI fee, GST, stamp duty and slippage. Sharpe uses a 6.5% risk-free rate; 'idle cash 0' assumes unused capital earns nothing (conservative), 'idle cash rf' assumes it earns the risk-free rate.

| strategy | trades | exposure | hit rate | avg trade bps | total return | CAGR | ann vol | Sharpe (idle cash 0) | Sharpe (idle cash rf) | max DD |
|---|---|---|---|---|---|---|---|---|---|---|
| model | 2720 | 72.1% | 45.8% | -6.6 | -85.0% | -11.9% | 11.2% | -1.65 | -1.07 | -85.1% |
| model_gross | 2720 | 72.1% | 49.5% | -1.4 | -38.3% | -3.2% | 11.2% | -0.81 | -0.23 | -49.2% |
| baseline_always_up | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| baseline_previous_day | 693 | 18.4% | 44.0% | -7.9 | -43.1% | -3.7% | 4.4% | -2.32 | -0.84 | -47.7% |
| baseline_ema_20_50 | 0 | 0.0% | — | — | 0.0% | 0.0% | 0.0% | — | — | 0.0% |
| always_long_intraday | 3771 | 100.0% | 43.8% | -11.2 | -98.7% | -25.2% | 13.4% | -2.58 | -2.10 | -98.8% |
| buy_and_hold | — | — | — | — | 357.2% | 10.7% | 16.3% | 0.31 | 0.70 | -38.4% |
| model_prev_close_entry ⚠ | 2720 | 72.1% | 61.1% | 23.4 | 50209.7% | 51.5% | 13.5% | 2.67 | 3.16 | -18.2% |

- `model`: p_model_lightgbm: long >= 0.55, short <= 0.45
- `model_gross`: same trades, no costs
- `always_long_intraday`: long every session open -> close
- `buy_and_hold`: index close to close, no costs
- `model_prev_close_entry`: NOT EXECUTABLE: enters at the previous close, before the forecast exists. Shows how much of the edge is the overnight gap.

### Threshold sensitivity (model, net)

| long ≥ / short ≤ | trades | hit rate | avg trade bps | CAGR | Sharpe (idle cash 0) | max DD |
|---|---|---|---|---|---|---|
| 0.50 / 0.50 | 3771 | 46.3% | -6.4 | -15.6% | -1.67 | -92.0% |
| 0.52 / 0.48 | 3312 | 46.2% | -6.3 | -13.7% | -1.61 | -89.0% |
| 0.55 / 0.45 | 2720 | 45.8% | -6.6 | -11.9% | -1.65 | -85.1% |
| 0.60 / 0.40 | 1728 | 45.6% | -5.7 | -6.8% | -1.45 | -69.7% |

### Model trades by regime and event

| subset | sessions | trades | hit rate | avg net bps | avg gross bps |
|---|---|---|---|---|---|
| vix_low | 711 | 545 | 47.0% | -3.9 | 1.2 |
| vix_normal | 2249 | 1587 | 44.5% | -7.6 | -2.4 |
| vix_high | 811 | 588 | 48.3% | -6.6 | -1.2 |
| is_expiry | 497 | 383 | 49.1% | -5.5 | -0.5 |
| not_is_expiry | 3274 | 2337 | 45.3% | -6.8 | -1.6 |
| is_monthly_expiry | 185 | 125 | 50.4% | -0.5 | 4.7 |
| not_is_monthly_expiry | 3586 | 2595 | 45.6% | -6.9 | -1.7 |
| is_rbi_policy | 25 | 22 | 59.1% | -5.8 | -0.8 |
| not_is_rbi_policy | 961 | 811 | 44.5% | -8.5 | -3.5 |
| is_union_budget | 17 | 12 | 41.7% | -23.6 | -18.4 |
| not_is_union_budget | 3754 | 2708 | 45.8% | -6.6 | -1.4 |
| is_election_results | 3 | 1 | 0.0% | -563.4 | -558.7 |
| not_is_election_results | 3768 | 2719 | 45.8% | -6.4 | -1.2 |

### Return by year

| year | model | model_gross | always_long_intraday | buy_and_hold |
|---|---|---|---|---|
| 2011 | -0.4% | 4.5% | -28.0% | -15.5% |
| 2012 | -10.4% | -4.2% | -7.7% | 27.7% |
| 2013 | -22.2% | -15.8% | -25.7% | 6.8% |
| 2014 | 9.8% | 15.7% | -12.0% | 31.4% |
| 2015 | -14.5% | -5.3% | -37.5% | -4.1% |
| 2016 | 7.2% | 18.2% | -29.7% | 3.0% |
| 2017 | -0.9% | 7.6% | -24.7% | 28.6% |
| 2018 | -22.2% | -14.2% | -27.2% | 3.2% |
| 2019 | -15.9% | -7.2% | -30.6% | 12.0% |
| 2020 | -4.6% | 5.7% | -35.0% | 14.9% |
| 2021 | -20.6% | -12.1% | -30.8% | 24.1% |
| 2022 | -17.1% | -8.1% | -14.2% | 4.3% |
| 2023 | -7.5% | 2.8% | -22.2% | 20.0% |
| 2024 | -20.3% | -11.7% | -23.9% | 8.4% |
| 2025 | -20.4% | -12.0% | -10.2% | 10.4% |
| 2026 | -10.2% | -3.2% | -13.9% | -3.8% |

### Warnings

- The model strategy loses money after costs over the test period.
