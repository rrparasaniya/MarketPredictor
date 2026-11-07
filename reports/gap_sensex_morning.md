## Gap up: sensex (morning run)

Out-of-sample 2014-01-20 to 2026-11-06: 3141 sessions, 50 walk-forward folds. Up-rate 0.437.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3141 | 0.679 | 0.634 | 0.630 | 0.744 | 0.203 | 0.591 | 0.023 |
| model_lightgbm | 3141 | 0.699 | 0.665 | 0.627 | 0.749 | 0.201 | 0.589 | 0.027 |
| baseline_base_rate | 3141 | 0.563 | 0.000 | 0.000 | 0.493 | 0.247 | 0.686 | 0.002 |
| baseline_previous_gap | 3141 | 0.563 | 0.000 | 0.000 | 0.497 | 0.247 | 0.686 | 0.002 |
| baseline_us_overnight | 3141 | 0.654 | 0.584 | 0.726 | 0.656 | 0.221 | 0.634 | 0.013 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0428, t=6.17), `model_lightgbm`=yes (+0.0445, t=7.01)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.686 / 0.731 | 0.689 / 0.721 | 0.650 / 0.462 | 0.650 / 0.473 | 0.613 / 0.625 |
| vix_normal | 1903 | 0.680 / 0.741 | 0.702 / 0.745 | 0.568 / 0.487 | 0.568 / 0.489 | 0.659 / 0.658 |
| vix_high | 527 | 0.664 / 0.719 | 0.698 / 0.746 | 0.425 / 0.506 | 0.425 / 0.484 | 0.693 / 0.694 |
| is_expiry | 293 | 0.703 / 0.732 | 0.713 / 0.738 | 0.621 / 0.553 | 0.621 / 0.555 | 0.638 / 0.670 |
| not_is_expiry | 2848 | 0.676 / 0.744 | 0.697 / 0.749 | 0.557 / 0.489 | 0.557 / 0.493 | 0.656 / 0.656 |
| is_monthly_expiry | 154 | 0.727 / 0.741 | 0.740 / 0.766 | 0.617 / 0.612 | 0.617 / 0.609 | 0.656 / 0.703 |
| not_is_monthly_expiry | 2987 | 0.676 / 0.744 | 0.696 / 0.748 | 0.560 / 0.488 | 0.560 / 0.491 | 0.654 / 0.654 |
| is_rbi_policy | 25 | 0.760 / 0.875 | 0.880 / 0.938 | 0.640 / 0.750 | 0.640 / 0.660 | 0.760 / 0.861 |
| not_is_rbi_policy | 959 | 0.728 / 0.786 | 0.732 / 0.769 | 0.636 / 0.553 | 0.636 / 0.560 | 0.654 / 0.707 |
| is_union_budget | 14 | 0.714 / 0.515 | 0.500 / 0.697 | 0.214 / 0.545 | 0.214 / 0.636 | 0.643 / 0.606 |
| not_is_union_budget | 3127 | 0.679 / 0.744 | 0.699 / 0.749 | 0.564 / 0.494 | 0.564 / 0.497 | 0.654 / 0.657 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3138 | 0.679 / 0.745 | 0.699 / 0.750 | 0.563 / 0.494 | 0.563 / 0.497 | 0.655 / 0.657 |

## Gap down: sensex (morning run)

Out-of-sample 2014-01-20 to 2026-11-06: 3141 sessions, 50 walk-forward folds. Up-rate 0.149.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3141 | 0.862 | 0.595 | 0.220 | 0.803 | 0.103 | 0.345 | 0.018 |
| model_lightgbm | 3141 | 0.866 | 0.605 | 0.284 | 0.814 | 0.099 | 0.329 | 0.017 |
| baseline_base_rate | 3141 | 0.851 | 0.000 | 0.000 | 0.469 | 0.128 | 0.425 | 0.005 |
| baseline_previous_gap | 3141 | 0.851 | 0.000 | 0.000 | 0.485 | 0.128 | 0.425 | 0.006 |
| baseline_us_overnight | 3141 | 0.851 | 0.000 | 0.000 | 0.677 | 0.118 | 0.385 | 0.015 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0403, t=5.66), `model_lightgbm`=yes (+0.0557, t=8.87)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.873 / 0.789 | 0.876 / 0.796 | 0.866 / 0.558 | 0.866 / 0.556 | 0.866 / 0.682 |
| vix_normal | 1903 | 0.869 / 0.820 | 0.870 / 0.829 | 0.858 / 0.481 | 0.858 / 0.486 | 0.858 / 0.692 |
| vix_high | 527 | 0.820 / 0.773 | 0.837 / 0.780 | 0.805 / 0.429 | 0.805 / 0.446 | 0.805 / 0.666 |
| is_expiry | 293 | 0.805 / 0.792 | 0.829 / 0.799 | 0.823 / 0.524 | 0.823 / 0.514 | 0.823 / 0.677 |
| not_is_expiry | 2848 | 0.867 / 0.802 | 0.869 / 0.815 | 0.854 / 0.463 | 0.854 / 0.481 | 0.854 / 0.677 |
| is_monthly_expiry | 154 | 0.851 / 0.879 | 0.903 / 0.873 | 0.864 / 0.490 | 0.864 / 0.474 | 0.864 / 0.717 |
| not_is_monthly_expiry | 2987 | 0.862 / 0.799 | 0.864 / 0.811 | 0.850 / 0.468 | 0.850 / 0.485 | 0.850 / 0.676 |
| is_rbi_policy | 25 | 0.920 / 0.792 | 0.840 / 0.958 | 0.960 / 0.188 | 0.960 / 0.062 | 0.960 / 0.479 |
| not_is_rbi_policy | 959 | 0.819 / 0.779 | 0.835 / 0.810 | 0.792 / 0.390 | 0.792 / 0.450 | 0.792 / 0.666 |
| is_union_budget | 14 | 0.929 / 0.769 | 0.857 / 0.846 | 0.929 / 0.000 | 0.929 / 0.000 | 0.929 / 0.615 |
| not_is_union_budget | 3127 | 0.861 / 0.803 | 0.866 / 0.814 | 0.851 / 0.470 | 0.851 / 0.486 | 0.851 / 0.678 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3138 | 0.862 / 0.805 | 0.866 / 0.815 | 0.851 / 0.469 | 0.851 / 0.485 | 0.851 / 0.679 |

