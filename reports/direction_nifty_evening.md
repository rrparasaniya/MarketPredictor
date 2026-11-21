## Direction: nifty (evening run)

Out-of-sample 2011-06-27 to 2026-11-20: 3776 sessions, 60 walk-forward folds. Up-rate 0.532.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3776 | 0.521 | 0.531 | 0.846 | 0.502 | 0.250 | 0.694 | 0.024 |
| model_lightgbm | 3776 | 0.526 | 0.536 | 0.807 | 0.521 | 0.250 | 0.693 | 0.025 |
| model_xgboost | 3776 | 0.527 | 0.536 | 0.823 | 0.518 | 0.250 | 0.692 | 0.021 |
| baseline_always_up | 3776 | 0.532 | 0.532 | 1.000 | 0.498 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3776 | 0.523 | 0.534 | 0.801 | 0.528 | 0.248 | 0.690 | 0.010 |
| baseline_ema_20_50 | 3776 | 0.530 | 0.531 | 0.986 | 0.501 | 0.249 | 0.692 | 0.011 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=no (-0.0046, t=-3.39), `model_lightgbm`=no (-0.0031, t=-1.96), `model_xgboost`=no (-0.0029, t=-1.92)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 712 | 0.534 / 0.545 | 0.527 / 0.550 | 0.537 / 0.557 | 0.538 / 0.489 | 0.542 / 0.539 | 0.538 / 0.477 |
| vix_normal | 2253 | 0.514 / 0.494 | 0.525 / 0.523 | 0.524 / 0.518 | 0.525 / 0.495 | 0.516 / 0.528 | 0.525 / 0.506 |
| vix_high | 811 | 0.529 / 0.496 | 0.528 / 0.505 | 0.527 / 0.503 | 0.546 / 0.505 | 0.524 / 0.512 | 0.536 / 0.494 |
| is_expiry | 498 | 0.508 / 0.540 | 0.534 / 0.576 | 0.532 / 0.571 | 0.500 / 0.476 | 0.526 / 0.544 | 0.502 / 0.479 |
| not_is_expiry | 3278 | 0.523 / 0.497 | 0.524 / 0.514 | 0.526 / 0.512 | 0.537 / 0.505 | 0.522 / 0.526 | 0.534 / 0.506 |
| is_monthly_expiry | 185 | 0.497 / 0.519 | 0.514 / 0.558 | 0.524 / 0.536 | 0.492 / 0.440 | 0.524 / 0.547 | 0.497 / 0.500 |
| not_is_monthly_expiry | 3591 | 0.522 / 0.501 | 0.526 / 0.519 | 0.527 / 0.517 | 0.534 / 0.501 | 0.522 / 0.527 | 0.532 / 0.501 |
| is_rbi_policy | 25 | 0.480 / 0.404 | 0.440 / 0.596 | 0.480 / 0.564 | 0.480 / 0.317 | 0.360 / 0.372 | 0.480 / 0.561 |
| not_is_rbi_policy | 961 | 0.530 / 0.537 | 0.544 / 0.549 | 0.534 / 0.544 | 0.532 / 0.477 | 0.524 / 0.539 | 0.532 / 0.511 |
| is_union_budget | 17 | 0.588 / 0.727 | 0.412 / 0.697 | 0.471 / 0.742 | 0.353 / 0.500 | 0.353 / 0.515 | 0.412 / 0.561 |
| not_is_union_budget | 3759 | 0.521 / 0.501 | 0.526 / 0.520 | 0.527 / 0.518 | 0.533 / 0.498 | 0.523 / 0.528 | 0.530 / 0.501 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3773 | 0.521 / 0.503 | 0.526 / 0.522 | 0.527 / 0.519 | 0.532 / 0.498 | 0.523 / 0.528 | 0.530 / 0.502 |

### Warnings

- model_logistic: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0046, t=-3.39 (needs > 0 and t >= 2.0).
- model_lightgbm: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0031, t=-1.96 (needs > 0 and t >= 2.0).
- model_xgboost: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0029, t=-1.92 (needs > 0 and t >= 2.0).

### Top features (final model)

- `tnx_ret_20`: 0.047
- `idx_gap`: 0.044
- `idx_rsi_14`: 0.040
- `bz_f_ret_5`: 0.035
- `dx_y_nyb_ret_5`: 0.033
- `dx_y_nyb_ret_20`: 0.033
- `idx_ret1_z`: 0.033
- `idx_range`: 0.033
- `bsesn_ret1_z`: 0.031
- `gspc_ret_5`: 0.027
- `idx_close_pos`: 0.025
- `inr_x_ret_1`: 0.022
- `nsebank_ret1_z`: 0.022
- `gc_f_ret_5`: 0.022
- `indiavix_level`: 0.020
