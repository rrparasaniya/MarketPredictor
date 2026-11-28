## Direction: nifty (evening run)

Out-of-sample 2011-06-27 to 2026-11-27: 3780 sessions, 60 walk-forward folds. Up-rate 0.532.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3780 | 0.521 | 0.531 | 0.846 | 0.502 | 0.251 | 0.694 | 0.025 |
| model_lightgbm | 3780 | 0.526 | 0.536 | 0.808 | 0.521 | 0.250 | 0.693 | 0.025 |
| model_xgboost | 3780 | 0.527 | 0.536 | 0.823 | 0.519 | 0.250 | 0.692 | 0.021 |
| baseline_always_up | 3780 | 0.532 | 0.532 | 1.000 | 0.498 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3780 | 0.522 | 0.534 | 0.801 | 0.527 | 0.248 | 0.690 | 0.010 |
| baseline_ema_20_50 | 3780 | 0.530 | 0.531 | 0.986 | 0.501 | 0.249 | 0.692 | 0.011 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=no (-0.0047, t=-3.42), `model_lightgbm`=no (-0.0031, t=-1.94), `model_xgboost`=no (-0.0028, t=-1.89)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 712 | 0.534 / 0.545 | 0.527 / 0.550 | 0.537 / 0.557 | 0.538 / 0.489 | 0.542 / 0.539 | 0.538 / 0.477 |
| vix_normal | 2257 | 0.514 / 0.493 | 0.525 / 0.522 | 0.524 / 0.518 | 0.525 / 0.494 | 0.515 / 0.527 | 0.525 / 0.506 |
| vix_high | 811 | 0.529 / 0.496 | 0.528 / 0.505 | 0.527 / 0.503 | 0.546 / 0.505 | 0.524 / 0.512 | 0.536 / 0.494 |
| is_expiry | 499 | 0.507 / 0.539 | 0.533 / 0.575 | 0.531 / 0.571 | 0.499 / 0.475 | 0.525 / 0.542 | 0.501 / 0.478 |
| not_is_expiry | 3281 | 0.523 / 0.497 | 0.525 / 0.514 | 0.526 / 0.512 | 0.537 / 0.505 | 0.522 / 0.526 | 0.534 / 0.506 |
| is_monthly_expiry | 186 | 0.495 / 0.516 | 0.511 / 0.556 | 0.522 / 0.536 | 0.489 / 0.437 | 0.522 / 0.542 | 0.495 / 0.496 |
| not_is_monthly_expiry | 3594 | 0.522 / 0.501 | 0.526 / 0.519 | 0.527 / 0.518 | 0.534 / 0.501 | 0.522 / 0.527 | 0.532 / 0.501 |
| is_rbi_policy | 25 | 0.480 / 0.404 | 0.440 / 0.596 | 0.480 / 0.564 | 0.480 / 0.317 | 0.360 / 0.372 | 0.480 / 0.561 |
| not_is_rbi_policy | 961 | 0.530 / 0.537 | 0.544 / 0.549 | 0.534 / 0.544 | 0.532 / 0.477 | 0.524 / 0.539 | 0.532 / 0.511 |
| is_union_budget | 17 | 0.588 / 0.727 | 0.412 / 0.697 | 0.471 / 0.742 | 0.353 / 0.500 | 0.353 / 0.515 | 0.412 / 0.561 |
| not_is_union_budget | 3763 | 0.520 / 0.500 | 0.526 / 0.520 | 0.527 / 0.518 | 0.533 / 0.498 | 0.523 / 0.527 | 0.530 / 0.501 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3777 | 0.521 / 0.502 | 0.526 / 0.522 | 0.527 / 0.519 | 0.532 / 0.498 | 0.522 / 0.528 | 0.530 / 0.502 |

### Warnings

- model_logistic: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0047, t=-3.42 (needs > 0 and t >= 2.0).
- model_lightgbm: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0031, t=-1.94 (needs > 0 and t >= 2.0).
- model_xgboost: does not clearly beat the best baseline (baseline_previous_day): log-loss gain -0.0028, t=-1.89 (needs > 0 and t >= 2.0).

### Top features (final model)

- `tnx_ret_20`: 0.053
- `idx_gap`: 0.046
- `idx_rsi_14`: 0.037
- `bsesn_ret1_z`: 0.035
- `idx_range`: 0.033
- `bz_f_ret_5`: 0.033
- `dx_y_nyb_ret_20`: 0.032
- `dx_y_nyb_ret_5`: 0.032
- `idx_close_pos`: 0.026
- `gspc_ret_5`: 0.026
- `nsebank_ret1_z`: 0.025
- `idx_ret1_z`: 0.025
- `idx_ret_1`: 0.024
- `gspc_ret_1`: 0.023
- `inr_x_ret_1`: 0.022
