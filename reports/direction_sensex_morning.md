## Direction: sensex (morning run)

Out-of-sample 2011-06-24 to 2026-11-13: 3776 sessions, 60 walk-forward folds. Up-rate 0.529.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3776 | 0.578 | 0.584 | 0.706 | 0.600 | 0.242 | 0.678 | 0.018 |
| model_lightgbm | 3776 | 0.582 | 0.586 | 0.709 | 0.606 | 0.241 | 0.674 | 0.018 |
| model_xgboost | 3776 | 0.581 | 0.584 | 0.716 | 0.607 | 0.240 | 0.674 | 0.022 |
| baseline_always_up | 3776 | 0.529 | 0.529 | 1.000 | 0.494 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3776 | 0.532 | 0.554 | 0.588 | 0.523 | 0.248 | 0.690 | 0.009 |
| baseline_ema_20_50 | 3776 | 0.524 | 0.527 | 0.953 | 0.495 | 0.249 | 0.692 | 0.009 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0119, t=3.15), `model_lightgbm`=yes (+0.0159, t=4.24), `model_xgboost`=yes (+0.0164, t=4.30)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 711 | 0.588 / 0.624 | 0.586 / 0.630 | 0.585 / 0.626 | 0.533 / 0.489 | 0.537 / 0.536 | 0.533 / 0.470 |
| vix_normal | 2252 | 0.575 / 0.595 | 0.582 / 0.598 | 0.585 / 0.603 | 0.522 / 0.491 | 0.532 / 0.518 | 0.522 / 0.496 |
| vix_high | 813 | 0.578 / 0.594 | 0.578 / 0.612 | 0.565 / 0.610 | 0.542 / 0.496 | 0.525 / 0.527 | 0.519 / 0.504 |
| is_expiry | 325 | 0.582 / 0.593 | 0.588 / 0.611 | 0.588 / 0.616 | 0.542 / 0.479 | 0.526 / 0.505 | 0.545 / 0.484 |
| not_is_expiry | 3451 | 0.578 / 0.601 | 0.581 / 0.605 | 0.580 / 0.606 | 0.527 / 0.495 | 0.532 / 0.524 | 0.522 / 0.495 |
| is_monthly_expiry | 185 | 0.595 / 0.610 | 0.605 / 0.627 | 0.600 / 0.631 | 0.541 / 0.464 | 0.535 / 0.516 | 0.546 / 0.450 |
| not_is_monthly_expiry | 3591 | 0.578 / 0.600 | 0.581 / 0.605 | 0.580 / 0.606 | 0.528 / 0.496 | 0.531 / 0.524 | 0.522 / 0.497 |
| is_rbi_policy | 25 | 0.600 / 0.538 | 0.640 / 0.660 | 0.640 / 0.660 | 0.520 / 0.349 | 0.560 / 0.458 | 0.520 / 0.465 |
| not_is_rbi_policy | 959 | 0.588 / 0.639 | 0.597 / 0.646 | 0.595 / 0.644 | 0.525 / 0.484 | 0.546 / 0.531 | 0.525 / 0.492 |
| is_union_budget | 16 | 0.625 / 0.571 | 0.562 / 0.651 | 0.562 / 0.635 | 0.438 / 0.540 | 0.688 / 0.667 | 0.562 / 0.492 |
| not_is_union_budget | 3760 | 0.578 / 0.600 | 0.582 / 0.606 | 0.581 / 0.607 | 0.529 / 0.494 | 0.531 / 0.522 | 0.523 / 0.495 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3773 | 0.579 / 0.600 | 0.582 / 0.606 | 0.581 / 0.608 | 0.529 / 0.495 | 0.532 / 0.523 | 0.524 / 0.495 |

### Top features (final model)

- `gspc_ret1_z`: 0.143
- `ixic_ret1_z`: 0.097
- `gspc_ret_1`: 0.065
- `ixic_ret_1`: 0.058
- `tnx_ret1_z`: 0.051
- `dx_y_nyb_ret_5`: 0.037
- `hsi_ret_20`: 0.031
- `idx_gap`: 0.028
- `nsei_ret1_z`: 0.025
- `idx_rsi_14`: 0.024
- `indiavix_chg_1`: 0.020
- `hsi_ret_5`: 0.017
- `gspc_ret_5`: 0.016
- `dx_y_nyb_ret1_z`: 0.016
- `idx_range`: 0.014
