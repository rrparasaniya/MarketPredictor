## Direction: sensex (evening run)

Out-of-sample 2011-06-24 to 2026-11-06: 3772 sessions, 60 walk-forward folds. Up-rate 0.528.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3772 | 0.522 | 0.531 | 0.822 | 0.502 | 0.251 | 0.695 | 0.024 |
| model_lightgbm | 3772 | 0.523 | 0.532 | 0.808 | 0.520 | 0.250 | 0.693 | 0.023 |
| model_xgboost | 3772 | 0.531 | 0.537 | 0.826 | 0.517 | 0.250 | 0.693 | 0.014 |
| baseline_always_up | 3772 | 0.528 | 0.528 | 1.000 | 0.494 | 0.249 | 0.692 | 0.009 |
| baseline_previous_day | 3772 | 0.531 | 0.553 | 0.587 | 0.523 | 0.249 | 0.690 | 0.009 |
| baseline_ema_20_50 | 3772 | 0.523 | 0.527 | 0.953 | 0.495 | 0.250 | 0.692 | 0.009 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=no (-0.0048, t=-3.01), `model_lightgbm`=no (-0.0026, t=-1.76), `model_xgboost`=no (-0.0025, t=-1.75)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 711 | 0.536 / 0.549 | 0.529 / 0.543 | 0.537 / 0.542 | 0.533 / 0.489 | 0.537 / 0.536 | 0.533 / 0.470 |
| vix_normal | 2248 | 0.515 / 0.491 | 0.513 / 0.516 | 0.524 / 0.518 | 0.522 / 0.490 | 0.532 / 0.518 | 0.522 / 0.496 |
| vix_high | 813 | 0.528 / 0.500 | 0.544 / 0.521 | 0.545 / 0.511 | 0.542 / 0.496 | 0.525 / 0.527 | 0.519 / 0.504 |
| is_expiry | 324 | 0.528 / 0.481 | 0.540 / 0.536 | 0.565 / 0.530 | 0.540 / 0.480 | 0.525 / 0.504 | 0.543 / 0.484 |
| not_is_expiry | 3448 | 0.521 / 0.504 | 0.521 / 0.518 | 0.528 / 0.516 | 0.527 / 0.495 | 0.532 / 0.524 | 0.521 / 0.495 |
| is_monthly_expiry | 185 | 0.535 / 0.479 | 0.541 / 0.507 | 0.584 / 0.499 | 0.541 / 0.464 | 0.535 / 0.516 | 0.546 / 0.450 |
| not_is_monthly_expiry | 3587 | 0.521 / 0.503 | 0.522 / 0.520 | 0.528 / 0.518 | 0.528 / 0.496 | 0.531 / 0.523 | 0.522 / 0.497 |
| is_rbi_policy | 25 | 0.560 / 0.397 | 0.440 / 0.532 | 0.520 / 0.538 | 0.520 / 0.349 | 0.560 / 0.458 | 0.520 / 0.465 |
| not_is_rbi_policy | 959 | 0.523 / 0.529 | 0.525 / 0.543 | 0.539 / 0.544 | 0.525 / 0.484 | 0.546 / 0.531 | 0.525 / 0.492 |
| is_union_budget | 16 | 0.688 / 0.635 | 0.500 / 0.730 | 0.500 / 0.746 | 0.438 / 0.540 | 0.688 / 0.667 | 0.562 / 0.492 |
| not_is_union_budget | 3756 | 0.521 / 0.501 | 0.523 / 0.519 | 0.531 / 0.516 | 0.529 / 0.494 | 0.531 / 0.522 | 0.523 / 0.495 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3769 | 0.522 / 0.503 | 0.523 / 0.520 | 0.531 / 0.518 | 0.529 / 0.494 | 0.531 / 0.523 | 0.523 / 0.495 |

### Warnings

- model_logistic: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0048, t=-3.01 (needs > 0 and t >= 2.0).
- model_lightgbm: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0026, t=-1.76 (needs > 0 and t >= 2.0).
- model_xgboost: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0025, t=-1.75 (needs > 0 and t >= 2.0).

### Top features (final model)

- `tnx_ret_20`: 0.052
- `idx_gap`: 0.036
- `idx_rsi_14`: 0.036
- `inr_x_ret_1`: 0.035
- `bz_f_ret_5`: 0.034
- `gspc_ret_5`: 0.032
- `bz_f_ret1_z`: 0.030
- `nsebank_ret1_z`: 0.030
- `dx_y_nyb_ret_5`: 0.027
- `gc_f_ret_20`: 0.027
- `nsei_ret_1`: 0.024
- `nsebank_ret_5`: 0.024
- `nsei_ret1_z`: 0.023
- `idx_ret1_z`: 0.023
- `days_to_next_session`: 0.020
