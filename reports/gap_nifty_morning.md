## Gap up: nifty (morning run)

Out-of-sample 2014-01-29 to 2026-11-20: 3145 sessions, 50 walk-forward folds. Up-rate 0.429.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3145 | 0.687 | 0.638 | 0.623 | 0.747 | 0.201 | 0.591 | 0.032 |
| model_lightgbm | 3145 | 0.697 | 0.655 | 0.618 | 0.746 | 0.201 | 0.590 | 0.028 |
| baseline_base_rate | 3145 | 0.571 | 0.000 | 0.000 | 0.495 | 0.245 | 0.684 | 0.002 |
| baseline_previous_gap | 3145 | 0.571 | 0.000 | 0.000 | 0.490 | 0.245 | 0.684 | 0.004 |
| baseline_us_overnight | 3145 | 0.653 | 0.576 | 0.728 | 0.654 | 0.220 | 0.631 | 0.007 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0408, t=6.10), `model_lightgbm`=yes (+0.0419, t=7.10)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.678 / 0.732 | 0.684 / 0.718 | 0.644 / 0.489 | 0.644 / 0.489 | 0.601 / 0.630 |
| vix_normal | 1906 | 0.699 / 0.755 | 0.715 / 0.756 | 0.577 / 0.493 | 0.577 / 0.485 | 0.670 / 0.671 |
| vix_high | 528 | 0.655 / 0.701 | 0.648 / 0.709 | 0.451 / 0.505 | 0.451 / 0.484 | 0.663 / 0.652 |
| is_expiry | 467 | 0.728 / 0.790 | 0.732 / 0.794 | 0.625 / 0.560 | 0.625 / 0.545 | 0.677 / 0.724 |
| not_is_expiry | 2678 | 0.680 / 0.740 | 0.690 / 0.739 | 0.562 / 0.490 | 0.562 / 0.487 | 0.649 / 0.646 |
| is_monthly_expiry | 154 | 0.714 / 0.759 | 0.721 / 0.778 | 0.695 / 0.556 | 0.695 / 0.523 | 0.649 / 0.687 |
| not_is_monthly_expiry | 2991 | 0.685 / 0.746 | 0.695 / 0.745 | 0.565 / 0.492 | 0.565 / 0.488 | 0.653 / 0.653 |
| is_rbi_policy | 25 | 0.880 / 0.849 | 0.800 / 0.849 | 0.720 / 0.746 | 0.720 / 0.575 | 0.680 / 0.734 |
| not_is_rbi_policy | 961 | 0.724 / 0.789 | 0.741 / 0.784 | 0.615 / 0.557 | 0.615 / 0.551 | 0.670 / 0.701 |
| is_union_budget | 15 | 0.333 / 0.500 | 0.467 / 0.589 | 0.467 / 0.643 | 0.467 / 0.536 | 0.467 / 0.536 |
| not_is_union_budget | 3130 | 0.688 / 0.749 | 0.698 / 0.747 | 0.572 / 0.494 | 0.572 / 0.490 | 0.654 / 0.655 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3142 | 0.687 / 0.748 | 0.697 / 0.747 | 0.571 / 0.495 | 0.571 / 0.490 | 0.654 / 0.655 |

## Gap down: nifty (morning run)

Out-of-sample 2014-01-29 to 2026-11-20: 3145 sessions, 50 walk-forward folds. Up-rate 0.184.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3145 | 0.837 | 0.646 | 0.249 | 0.782 | 0.121 | 0.396 | 0.019 |
| model_lightgbm | 3145 | 0.835 | 0.605 | 0.299 | 0.782 | 0.120 | 0.392 | 0.026 |
| baseline_base_rate | 3145 | 0.816 | 0.000 | 0.000 | 0.441 | 0.152 | 0.484 | 0.038 |
| baseline_previous_gap | 3145 | 0.816 | 0.000 | 0.000 | 0.469 | 0.152 | 0.484 | 0.030 |
| baseline_us_overnight | 3145 | 0.816 | 0.000 | 0.000 | 0.673 | 0.138 | 0.435 | 0.029 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0384, t=5.51), `model_lightgbm`=yes (+0.0428, t=7.00)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.869 / 0.769 | 0.866 / 0.765 | 0.851 / 0.433 | 0.851 / 0.454 | 0.851 / 0.651 |
| vix_normal | 1906 | 0.833 / 0.789 | 0.829 / 0.788 | 0.813 / 0.460 | 0.813 / 0.484 | 0.813 / 0.685 |
| vix_high | 528 | 0.807 / 0.767 | 0.814 / 0.769 | 0.780 / 0.389 | 0.780 / 0.413 | 0.780 / 0.659 |
| is_expiry | 467 | 0.822 / 0.806 | 0.846 / 0.808 | 0.788 / 0.469 | 0.788 / 0.479 | 0.788 / 0.697 |
| not_is_expiry | 2678 | 0.839 / 0.777 | 0.833 / 0.777 | 0.821 / 0.442 | 0.821 / 0.472 | 0.821 / 0.671 |
| is_monthly_expiry | 154 | 0.864 / 0.876 | 0.896 / 0.853 | 0.825 / 0.435 | 0.825 / 0.450 | 0.825 / 0.660 |
| not_is_monthly_expiry | 2991 | 0.835 / 0.778 | 0.832 / 0.779 | 0.815 / 0.441 | 0.815 / 0.470 | 0.815 / 0.674 |
| is_rbi_policy | 25 | 0.920 / 0.717 | 0.840 / 0.870 | 0.920 / 0.315 | 0.920 / 0.120 | 0.920 / 0.554 |
| not_is_rbi_policy | 961 | 0.824 / 0.801 | 0.839 / 0.807 | 0.786 / 0.424 | 0.786 / 0.473 | 0.786 / 0.677 |
| is_union_budget | 15 | 0.933 / 0.714 | 0.867 / 0.929 | 0.933 / 0.071 | 0.933 / 0.000 | 0.933 / 0.571 |
| not_is_union_budget | 3130 | 0.836 / 0.782 | 0.835 / 0.782 | 0.815 / 0.442 | 0.815 / 0.470 | 0.815 / 0.674 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3142 | 0.837 / 0.784 | 0.835 / 0.783 | 0.816 / 0.441 | 0.816 / 0.469 | 0.816 / 0.675 |

