## Direction: nifty (morning run)

Out-of-sample 2011-06-27 to 2026-11-06: 3767 sessions, 60 walk-forward folds. Up-rate 0.531.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3767 | 0.587 | 0.592 | 0.723 | 0.603 | 0.241 | 0.676 | 0.020 |
| model_lightgbm | 3767 | 0.591 | 0.596 | 0.713 | 0.612 | 0.240 | 0.673 | 0.014 |
| model_xgboost | 3767 | 0.593 | 0.598 | 0.719 | 0.613 | 0.240 | 0.673 | 0.018 |
| baseline_always_up | 3767 | 0.531 | 0.531 | 1.000 | 0.497 | 0.249 | 0.692 | 0.010 |
| baseline_previous_day | 3767 | 0.522 | 0.534 | 0.801 | 0.528 | 0.248 | 0.690 | 0.010 |
| baseline_ema_20_50 | 3767 | 0.529 | 0.531 | 0.986 | 0.500 | 0.249 | 0.692 | 0.010 |

Best baseline (log loss): `baseline_previous_day`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0134, t=3.75), `model_lightgbm`=yes (+0.0165, t=4.33), `model_xgboost`=yes (+0.0171, t=4.45)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | model_xgboost | baseline_always_up | baseline_previous_day | baseline_ema_20_50 |
|---|---|---|---|---|---|---|---|
| vix_low | 711 | 0.602 / 0.635 | 0.591 / 0.639 | 0.595 / 0.642 | 0.539 / 0.488 | 0.543 / 0.540 | 0.539 / 0.476 |
| vix_normal | 2245 | 0.583 / 0.596 | 0.598 / 0.607 | 0.596 / 0.607 | 0.524 / 0.493 | 0.515 / 0.528 | 0.524 / 0.504 |
| vix_high | 811 | 0.587 / 0.599 | 0.572 / 0.610 | 0.583 / 0.611 | 0.546 / 0.505 | 0.524 / 0.512 | 0.536 / 0.494 |
| is_expiry | 496 | 0.591 / 0.648 | 0.619 / 0.669 | 0.625 / 0.667 | 0.498 / 0.475 | 0.524 / 0.542 | 0.500 / 0.477 |
| not_is_expiry | 3271 | 0.587 / 0.598 | 0.587 / 0.604 | 0.589 / 0.605 | 0.537 / 0.505 | 0.522 / 0.526 | 0.534 / 0.506 |
| is_monthly_expiry | 185 | 0.551 / 0.609 | 0.595 / 0.626 | 0.595 / 0.633 | 0.492 / 0.440 | 0.524 / 0.547 | 0.497 / 0.500 |
| not_is_monthly_expiry | 3582 | 0.589 / 0.604 | 0.591 / 0.611 | 0.593 / 0.612 | 0.534 / 0.500 | 0.522 / 0.527 | 0.531 / 0.500 |
| is_rbi_policy | 25 | 0.560 / 0.564 | 0.720 / 0.686 | 0.720 / 0.686 | 0.480 / 0.317 | 0.360 / 0.372 | 0.480 / 0.561 |
| not_is_rbi_policy | 961 | 0.600 / 0.637 | 0.604 / 0.639 | 0.610 / 0.643 | 0.532 / 0.477 | 0.524 / 0.539 | 0.532 / 0.511 |
| is_union_budget | 17 | 0.529 / 0.500 | 0.529 / 0.606 | 0.471 / 0.576 | 0.353 / 0.500 | 0.353 / 0.515 | 0.412 / 0.561 |
| not_is_union_budget | 3750 | 0.588 / 0.603 | 0.591 / 0.612 | 0.594 / 0.614 | 0.532 / 0.497 | 0.523 / 0.528 | 0.530 / 0.500 |
| is_election_results | 3 | — | — | — | — | — | — |
| not_is_election_results | 3764 | 0.588 / 0.603 | 0.591 / 0.612 | 0.594 / 0.614 | 0.532 / 0.498 | 0.523 / 0.528 | 0.529 / 0.501 |

### Top features (final model)

- `gspc_ret1_z`: 0.154
- `ixic_ret1_z`: 0.075
- `gspc_ret_1`: 0.072
- `ixic_ret_1`: 0.047
- `tnx_ret1_z`: 0.046
- `dx_y_nyb_ret_5`: 0.037
- `hsi_ret_20`: 0.032
- `idx_gap`: 0.028
- `idx_rsi_14`: 0.024
- `gspc_ret_5`: 0.023
- `dx_y_nyb_ret1_z`: 0.023
- `tnx_ret_5`: 0.019
- `idx_ret1_z`: 0.019
- `bsesn_ret1_z`: 0.018
- `idx_range`: 0.018
