## Direction: sensex (morning run)

Out-of-sample 2011-06-24 to 2026-11-27: 3785 sessions, 61 walk-forward folds. Up-rate 0.529.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3785 | 0.578 | 0.584 | 0.704 | 0.599 | 0.242 | 0.678 | 0.017 |
| model_lightgbm | 3785 | 0.582 | 0.586 | 0.708 | 0.605 | 0.241 | 0.674 | 0.018 |
| model_xgboost | 3785 | 0.580 | 0.584 | 0.715 | 0.607 | 0.240 | 0.674 | 0.023 |
| baseline_always_up | 3785 | 0.529 | 0.529 | 1.000 | 0.494 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3785 | 0.531 | 0.553 | 0.587 | 0.522 | 0.249 | 0.690 | 0.010 |
| baseline_ema_20_50 | 3785 | 0.524 | 0.528 | 0.953 | 0.495 | 0.249 | 0.692 | 0.010 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0119, t=3.15), `model_lightgbm`=yes (+0.0158, t=4.21), `model_xgboost`=yes (+0.0163, t=4.28)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 711 | 0.588 / 0.624 | 0.586 / 0.630 | 0.585 / 0.626 | 0.533 / 0.489 | 0.537 / 0.536 | 0.533 / 0.470 |
| vix_normal | 2261 | 0.575 / 0.595 | 0.581 / 0.597 | 0.585 / 0.602 | 0.523 / 0.491 | 0.531 / 0.517 | 0.523 / 0.497 |
| vix_high | 813 | 0.578 / 0.594 | 0.578 / 0.612 | 0.565 / 0.610 | 0.542 / 0.496 | 0.525 / 0.527 | 0.519 / 0.504 |
| is_expiry | 327 | 0.581 / 0.591 | 0.587 / 0.610 | 0.587 / 0.616 | 0.544 / 0.479 | 0.526 / 0.505 | 0.547 / 0.486 |
| not_is_expiry | 3458 | 0.578 / 0.600 | 0.581 / 0.605 | 0.580 / 0.606 | 0.527 / 0.495 | 0.532 / 0.524 | 0.522 / 0.495 |
| is_monthly_expiry | 186 | 0.597 / 0.611 | 0.608 / 0.629 | 0.602 / 0.633 | 0.543 / 0.466 | 0.538 / 0.519 | 0.548 / 0.453 |
| not_is_monthly_expiry | 3599 | 0.577 / 0.599 | 0.580 / 0.604 | 0.579 / 0.605 | 0.528 / 0.496 | 0.531 / 0.523 | 0.523 / 0.497 |
| is_rbi_policy | 25 | 0.600 / 0.538 | 0.640 / 0.660 | 0.640 / 0.660 | 0.520 / 0.349 | 0.560 / 0.458 | 0.520 / 0.465 |
| not_is_rbi_policy | 959 | 0.588 / 0.639 | 0.597 / 0.646 | 0.595 / 0.644 | 0.525 / 0.484 | 0.546 / 0.531 | 0.525 / 0.492 |
| is_union_budget | 16 | 0.625 / 0.571 | 0.562 / 0.651 | 0.562 / 0.635 | 0.438 / 0.540 | 0.688 / 0.667 | 0.562 / 0.492 |
| not_is_union_budget | 3769 | 0.578 / 0.599 | 0.582 / 0.605 | 0.581 / 0.607 | 0.529 / 0.494 | 0.530 / 0.522 | 0.524 / 0.495 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3782 | 0.578 / 0.600 | 0.582 / 0.606 | 0.581 / 0.607 | 0.529 / 0.495 | 0.531 / 0.523 | 0.524 / 0.496 |

### Top features (final model)

- `gspc_ret1_z`: 0.160
- `ixic_ret1_z`: 0.087
- `gspc_ret_1`: 0.060
- `ixic_ret_1`: 0.059
- `tnx_ret1_z`: 0.051
- `dx_y_nyb_ret_5`: 0.040
- `hsi_ret_20`: 0.036
- `idx_gap`: 0.026
- `nsei_ret1_z`: 0.024
- `idx_rsi_14`: 0.023
- `hsi_ret_5`: 0.019
- `indiavix_chg_1`: 0.019
- `gspc_ret_5`: 0.017
- `dx_y_nyb_ret1_z`: 0.017
- `tnx_ret_5`: 0.013
