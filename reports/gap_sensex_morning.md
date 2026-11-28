## Gap up: sensex (morning run)

Out-of-sample 2014-01-20 to 2026-11-27: 3154 sessions, 51 walk-forward folds. Up-rate 0.438.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3154 | 0.679 | 0.634 | 0.628 | 0.744 | 0.203 | 0.592 | 0.023 |
| model_lightgbm | 3154 | 0.698 | 0.664 | 0.625 | 0.748 | 0.202 | 0.590 | 0.026 |
| baseline_base_rate | 3154 | 0.562 | 0.000 | 0.000 | 0.493 | 0.247 | 0.686 | 0.002 |
| baseline_previous_gap | 3154 | 0.562 | 0.000 | 0.000 | 0.497 | 0.247 | 0.686 | 0.001 |
| baseline_us_overnight | 3154 | 0.654 | 0.584 | 0.723 | 0.655 | 0.221 | 0.634 | 0.013 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0428, t=6.19), `model_lightgbm`=yes (+0.0443, t=7.00)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.686 / 0.731 | 0.689 / 0.721 | 0.650 / 0.462 | 0.650 / 0.473 | 0.613 / 0.625 |
| vix_normal | 1916 | 0.680 / 0.740 | 0.700 / 0.743 | 0.568 / 0.487 | 0.568 / 0.489 | 0.658 / 0.656 |
| vix_high | 527 | 0.664 / 0.719 | 0.698 / 0.746 | 0.425 / 0.506 | 0.425 / 0.484 | 0.693 / 0.694 |
| is_expiry | 296 | 0.703 / 0.732 | 0.709 / 0.736 | 0.622 / 0.553 | 0.622 / 0.556 | 0.635 / 0.666 |
| not_is_expiry | 2858 | 0.676 / 0.743 | 0.696 / 0.748 | 0.556 / 0.489 | 0.556 / 0.493 | 0.656 / 0.655 |
| is_monthly_expiry | 155 | 0.723 / 0.741 | 0.735 / 0.762 | 0.613 / 0.609 | 0.613 / 0.610 | 0.652 / 0.696 |
| not_is_monthly_expiry | 2999 | 0.676 / 0.743 | 0.696 / 0.747 | 0.560 / 0.488 | 0.560 / 0.491 | 0.654 / 0.653 |
| is_rbi_policy | 25 | 0.760 / 0.875 | 0.880 / 0.938 | 0.640 / 0.750 | 0.640 / 0.660 | 0.760 / 0.861 |
| not_is_rbi_policy | 959 | 0.728 / 0.786 | 0.732 / 0.769 | 0.636 / 0.553 | 0.636 / 0.560 | 0.654 / 0.707 |
| is_union_budget | 14 | 0.714 / 0.515 | 0.500 / 0.697 | 0.214 / 0.545 | 0.214 / 0.636 | 0.643 / 0.606 |
| not_is_union_budget | 3140 | 0.678 / 0.743 | 0.698 / 0.748 | 0.564 / 0.493 | 0.564 / 0.497 | 0.654 / 0.656 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3151 | 0.679 / 0.744 | 0.698 / 0.748 | 0.563 / 0.494 | 0.563 / 0.498 | 0.654 / 0.656 |

## Gap down: sensex (morning run)

Out-of-sample 2014-01-20 to 2026-11-27: 3154 sessions, 51 walk-forward folds. Up-rate 0.149.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3154 | 0.861 | 0.595 | 0.219 | 0.802 | 0.103 | 0.345 | 0.018 |
| model_lightgbm | 3154 | 0.866 | 0.604 | 0.285 | 0.813 | 0.099 | 0.330 | 0.016 |
| baseline_base_rate | 3154 | 0.851 | 0.000 | 0.000 | 0.469 | 0.128 | 0.425 | 0.005 |
| baseline_previous_gap | 3154 | 0.851 | 0.000 | 0.000 | 0.484 | 0.128 | 0.425 | 0.006 |
| baseline_us_overnight | 3154 | 0.851 | 0.000 | 0.000 | 0.677 | 0.119 | 0.385 | 0.015 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0400, t=5.63), `model_lightgbm`=yes (+0.0552, t=8.81)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.873 / 0.789 | 0.876 / 0.796 | 0.866 / 0.558 | 0.866 / 0.556 | 0.866 / 0.682 |
| vix_normal | 1916 | 0.868 / 0.818 | 0.870 / 0.827 | 0.858 / 0.480 | 0.858 / 0.485 | 0.858 / 0.691 |
| vix_high | 527 | 0.820 / 0.773 | 0.837 / 0.780 | 0.805 / 0.429 | 0.805 / 0.446 | 0.805 / 0.666 |
| is_expiry | 296 | 0.807 / 0.792 | 0.831 / 0.798 | 0.824 / 0.519 | 0.824 / 0.511 | 0.824 / 0.673 |
| not_is_expiry | 2858 | 0.867 / 0.801 | 0.869 / 0.814 | 0.854 / 0.464 | 0.854 / 0.481 | 0.854 / 0.677 |
| is_monthly_expiry | 155 | 0.852 / 0.880 | 0.903 / 0.873 | 0.865 / 0.488 | 0.865 / 0.473 | 0.865 / 0.713 |
| not_is_monthly_expiry | 2999 | 0.862 / 0.798 | 0.864 / 0.811 | 0.850 / 0.468 | 0.850 / 0.485 | 0.850 / 0.675 |
| is_rbi_policy | 25 | 0.920 / 0.792 | 0.840 / 0.958 | 0.960 / 0.188 | 0.960 / 0.062 | 0.960 / 0.479 |
| not_is_rbi_policy | 959 | 0.819 / 0.779 | 0.835 / 0.810 | 0.792 / 0.390 | 0.792 / 0.450 | 0.792 / 0.666 |
| is_union_budget | 14 | 0.929 / 0.769 | 0.857 / 0.846 | 0.929 / 0.000 | 0.929 / 0.000 | 0.929 / 0.615 |
| not_is_union_budget | 3140 | 0.861 / 0.802 | 0.866 / 0.813 | 0.851 / 0.470 | 0.851 / 0.486 | 0.851 / 0.677 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3151 | 0.862 / 0.804 | 0.866 / 0.814 | 0.851 / 0.469 | 0.851 / 0.485 | 0.851 / 0.678 |

