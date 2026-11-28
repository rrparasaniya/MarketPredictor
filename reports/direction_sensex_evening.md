## Direction: sensex (evening run)

Out-of-sample 2011-06-24 to 2026-11-27: 3785 sessions, 61 walk-forward folds. Up-rate 0.529.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3785 | 0.522 | 0.531 | 0.822 | 0.503 | 0.251 | 0.695 | 0.024 |
| model_lightgbm | 3785 | 0.523 | 0.533 | 0.809 | 0.520 | 0.250 | 0.693 | 0.023 |
| model_xgboost | 3785 | 0.532 | 0.537 | 0.827 | 0.517 | 0.250 | 0.693 | 0.013 |
| baseline_always_up | 3785 | 0.529 | 0.529 | 1.000 | 0.494 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3785 | 0.531 | 0.553 | 0.587 | 0.522 | 0.249 | 0.690 | 0.010 |
| baseline_ema_20_50 | 3785 | 0.524 | 0.528 | 0.953 | 0.495 | 0.249 | 0.692 | 0.010 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=no (-0.0047, t=-2.92), `model_lightgbm`=no (-0.0025, t=-1.70), `model_xgboost`=no (-0.0024, t=-1.70)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 711 | 0.536 / 0.549 | 0.529 / 0.543 | 0.537 / 0.542 | 0.533 / 0.489 | 0.537 / 0.536 | 0.533 / 0.470 |
| vix_normal | 2261 | 0.516 / 0.492 | 0.514 / 0.517 | 0.525 / 0.518 | 0.523 / 0.491 | 0.531 / 0.517 | 0.523 / 0.497 |
| vix_high | 813 | 0.528 / 0.500 | 0.544 / 0.521 | 0.545 / 0.511 | 0.542 / 0.496 | 0.525 / 0.527 | 0.519 / 0.504 |
| is_expiry | 327 | 0.532 / 0.482 | 0.544 / 0.536 | 0.569 / 0.531 | 0.544 / 0.479 | 0.526 / 0.505 | 0.547 / 0.486 |
| not_is_expiry | 3458 | 0.521 / 0.504 | 0.521 / 0.518 | 0.528 / 0.516 | 0.527 / 0.495 | 0.532 / 0.524 | 0.522 / 0.495 |
| is_monthly_expiry | 186 | 0.538 / 0.481 | 0.543 / 0.509 | 0.586 / 0.501 | 0.543 / 0.466 | 0.538 / 0.519 | 0.548 / 0.453 |
| not_is_monthly_expiry | 3599 | 0.521 / 0.504 | 0.522 / 0.521 | 0.529 / 0.518 | 0.528 / 0.496 | 0.531 / 0.523 | 0.523 / 0.497 |
| is_rbi_policy | 25 | 0.560 / 0.397 | 0.440 / 0.532 | 0.520 / 0.538 | 0.520 / 0.349 | 0.560 / 0.458 | 0.520 / 0.465 |
| not_is_rbi_policy | 959 | 0.523 / 0.529 | 0.525 / 0.543 | 0.539 / 0.544 | 0.525 / 0.484 | 0.546 / 0.531 | 0.525 / 0.492 |
| is_union_budget | 16 | 0.688 / 0.635 | 0.500 / 0.730 | 0.500 / 0.746 | 0.438 / 0.540 | 0.688 / 0.667 | 0.562 / 0.492 |
| not_is_union_budget | 3769 | 0.521 / 0.502 | 0.523 / 0.519 | 0.532 / 0.516 | 0.529 / 0.494 | 0.530 / 0.522 | 0.524 / 0.495 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3782 | 0.522 / 0.503 | 0.524 / 0.521 | 0.532 / 0.518 | 0.529 / 0.495 | 0.531 / 0.523 | 0.524 / 0.496 |

### Warnings

- model_logistic: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0047, t=-2.92 (needs > 0 and t >= 2.0).
- model_lightgbm: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0025, t=-1.70 (needs > 0 and t >= 2.0).
- model_xgboost: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0024, t=-1.70 (needs > 0 and t >= 2.0).

### Top features (final model)

- `tnx_ret_20`: 0.053
- `idx_rsi_14`: 0.041
- `idx_gap`: 0.041
- `nsebank_ret1_z`: 0.033
- `bz_f_ret_5`: 0.030
- `gspc_ret_5`: 0.030
- `bz_f_ret1_z`: 0.026
- `dx_y_nyb_ret_5`: 0.026
- `nsei_ret_1`: 0.025
- `nsei_ret1_z`: 0.023
- `gc_f_ret_5`: 0.023
- `inr_x_ret_1`: 0.023
- `inr_x_ret1_z`: 0.022
- `gc_f_ret_20`: 0.021
- `idx_range`: 0.020
