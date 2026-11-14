## Direction: sensex (evening run)

Out-of-sample 2011-06-24 to 2026-11-13: 3776 sessions, 60 walk-forward folds. Up-rate 0.529.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3776 | 0.522 | 0.531 | 0.822 | 0.503 | 0.251 | 0.695 | 0.024 |
| model_lightgbm | 3776 | 0.523 | 0.532 | 0.808 | 0.520 | 0.250 | 0.693 | 0.023 |
| model_xgboost | 3776 | 0.531 | 0.537 | 0.826 | 0.518 | 0.250 | 0.693 | 0.014 |
| baseline_always_up | 3776 | 0.529 | 0.529 | 1.000 | 0.494 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3776 | 0.532 | 0.554 | 0.588 | 0.523 | 0.248 | 0.690 | 0.009 |
| baseline_ema_20_50 | 3776 | 0.524 | 0.527 | 0.953 | 0.495 | 0.249 | 0.692 | 0.009 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=no (-0.0047, t=-2.94), `model_lightgbm`=no (-0.0026, t=-1.74), `model_xgboost`=no (-0.0024, t=-1.72)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 711 | 0.536 / 0.549 | 0.529 / 0.543 | 0.537 / 0.542 | 0.533 / 0.489 | 0.537 / 0.536 | 0.533 / 0.470 |
| vix_normal | 2252 | 0.516 / 0.493 | 0.514 / 0.517 | 0.524 / 0.519 | 0.522 / 0.491 | 0.532 / 0.518 | 0.522 / 0.496 |
| vix_high | 813 | 0.528 / 0.500 | 0.544 / 0.521 | 0.545 / 0.511 | 0.542 / 0.496 | 0.525 / 0.527 | 0.519 / 0.504 |
| is_expiry | 325 | 0.529 / 0.482 | 0.542 / 0.537 | 0.566 / 0.532 | 0.542 / 0.479 | 0.526 / 0.505 | 0.545 / 0.484 |
| not_is_expiry | 3451 | 0.521 / 0.505 | 0.521 / 0.519 | 0.528 / 0.516 | 0.527 / 0.495 | 0.532 / 0.524 | 0.522 / 0.495 |
| is_monthly_expiry | 185 | 0.535 / 0.479 | 0.541 / 0.507 | 0.584 / 0.499 | 0.541 / 0.464 | 0.535 / 0.516 | 0.546 / 0.450 |
| not_is_monthly_expiry | 3591 | 0.521 / 0.504 | 0.522 / 0.521 | 0.529 / 0.519 | 0.528 / 0.496 | 0.531 / 0.524 | 0.522 / 0.497 |
| is_rbi_policy | 25 | 0.560 / 0.397 | 0.440 / 0.532 | 0.520 / 0.538 | 0.520 / 0.349 | 0.560 / 0.458 | 0.520 / 0.465 |
| not_is_rbi_policy | 959 | 0.523 / 0.529 | 0.525 / 0.543 | 0.539 / 0.544 | 0.525 / 0.484 | 0.546 / 0.531 | 0.525 / 0.492 |
| is_union_budget | 16 | 0.688 / 0.635 | 0.500 / 0.730 | 0.500 / 0.746 | 0.438 / 0.540 | 0.688 / 0.667 | 0.562 / 0.492 |
| not_is_union_budget | 3760 | 0.521 / 0.502 | 0.523 / 0.519 | 0.531 / 0.517 | 0.529 / 0.494 | 0.531 / 0.522 | 0.523 / 0.495 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3773 | 0.522 / 0.504 | 0.523 / 0.521 | 0.531 / 0.518 | 0.529 / 0.495 | 0.532 / 0.523 | 0.524 / 0.495 |

### Warnings

- model_logistic: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0047, t=-2.94 (needs > 0 and t >= 2.0).
- model_lightgbm: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0026, t=-1.74 (needs > 0 and t >= 2.0).
- model_xgboost: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0024, t=-1.72 (needs > 0 and t >= 2.0).

### Top features (final model)

- `tnx_ret_20`: 0.047
- `idx_gap`: 0.035
- `idx_rsi_14`: 0.034
- `bz_f_ret_5`: 0.032
- `nsebank_ret1_z`: 0.031
- `gspc_ret_5`: 0.030
- `inr_x_ret_1`: 0.029
- `bz_f_ret1_z`: 0.029
- `inr_x_ret1_z`: 0.028
- `nsei_ret1_z`: 0.027
- `dx_y_nyb_ret_5`: 0.026
- `nsebank_ret_5`: 0.024
- `dx_y_nyb_ret_20`: 0.023
- `idx_range`: 0.022
- `gc_f_ret_20`: 0.022
