## Direction: sensex (morning run)

Out-of-sample 2011-06-24 to 2026-11-20: 3781 sessions, 61 walk-forward folds. Up-rate 0.529.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3781 | 0.578 | 0.584 | 0.705 | 0.599 | 0.242 | 0.678 | 0.018 |
| model_lightgbm | 3781 | 0.581 | 0.586 | 0.708 | 0.605 | 0.241 | 0.674 | 0.019 |
| model_xgboost | 3781 | 0.580 | 0.584 | 0.715 | 0.607 | 0.241 | 0.674 | 0.023 |
| baseline_always_up | 3781 | 0.529 | 0.529 | 1.000 | 0.495 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3781 | 0.531 | 0.554 | 0.588 | 0.523 | 0.248 | 0.690 | 0.010 |
| baseline_ema_20_50 | 3781 | 0.524 | 0.528 | 0.953 | 0.495 | 0.249 | 0.692 | 0.010 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0118, t=3.12), `model_lightgbm`=yes (+0.0156, t=4.17), `model_xgboost`=yes (+0.0162, t=4.25)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 711 | 0.588 / 0.624 | 0.586 / 0.630 | 0.585 / 0.626 | 0.533 / 0.489 | 0.537 / 0.536 | 0.533 / 0.470 |
| vix_normal | 2257 | 0.575 / 0.594 | 0.581 / 0.597 | 0.584 / 0.602 | 0.523 / 0.491 | 0.532 / 0.518 | 0.523 / 0.497 |
| vix_high | 813 | 0.578 / 0.594 | 0.578 / 0.612 | 0.565 / 0.610 | 0.542 / 0.496 | 0.525 / 0.527 | 0.519 / 0.504 |
| is_expiry | 326 | 0.580 / 0.591 | 0.586 / 0.609 | 0.586 / 0.615 | 0.543 / 0.479 | 0.525 / 0.504 | 0.546 / 0.485 |
| not_is_expiry | 3455 | 0.578 / 0.600 | 0.581 / 0.605 | 0.580 / 0.606 | 0.528 / 0.496 | 0.532 / 0.524 | 0.522 / 0.495 |
| is_monthly_expiry | 185 | 0.595 / 0.610 | 0.605 / 0.627 | 0.600 / 0.631 | 0.541 / 0.464 | 0.535 / 0.516 | 0.546 / 0.450 |
| not_is_monthly_expiry | 3596 | 0.577 / 0.599 | 0.580 / 0.604 | 0.579 / 0.605 | 0.528 / 0.496 | 0.531 / 0.523 | 0.523 / 0.498 |
| is_rbi_policy | 25 | 0.600 / 0.538 | 0.640 / 0.660 | 0.640 / 0.660 | 0.520 / 0.349 | 0.560 / 0.458 | 0.520 / 0.465 |
| not_is_rbi_policy | 959 | 0.588 / 0.639 | 0.597 / 0.646 | 0.595 / 0.644 | 0.525 / 0.484 | 0.546 / 0.531 | 0.525 / 0.492 |
| is_union_budget | 16 | 0.625 / 0.571 | 0.562 / 0.651 | 0.562 / 0.635 | 0.438 / 0.540 | 0.688 / 0.667 | 0.562 / 0.492 |
| not_is_union_budget | 3765 | 0.578 / 0.599 | 0.581 / 0.605 | 0.580 / 0.607 | 0.529 / 0.494 | 0.531 / 0.522 | 0.524 / 0.495 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3778 | 0.578 / 0.600 | 0.582 / 0.606 | 0.581 / 0.607 | 0.529 / 0.495 | 0.531 / 0.523 | 0.524 / 0.496 |

### Top features (final model)

- `gspc_ret1_z`: 0.153
- `ixic_ret1_z`: 0.089
- `gspc_ret_1`: 0.062
- `ixic_ret_1`: 0.061
- `tnx_ret1_z`: 0.055
- `dx_y_nyb_ret_5`: 0.035
- `hsi_ret_20`: 0.033
- `idx_gap`: 0.028
- `idx_rsi_14`: 0.022
- `indiavix_chg_1`: 0.018
- `nsei_ret1_z`: 0.017
- `hsi_ret_5`: 0.017
- `tnx_ret_5`: 0.015
- `inr_x_ret_5`: 0.015
- `inr_x_ret_20`: 0.014
