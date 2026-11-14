## Gap up: nifty (morning run)

Out-of-sample 2014-01-29 to 2026-11-13: 3140 sessions, 50 walk-forward folds. Up-rate 0.429.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3140 | 0.687 | 0.638 | 0.623 | 0.747 | 0.201 | 0.591 | 0.032 |
| model_lightgbm | 3140 | 0.696 | 0.655 | 0.619 | 0.746 | 0.202 | 0.590 | 0.028 |
| baseline_base_rate | 3140 | 0.571 | 0.000 | 0.000 | 0.495 | 0.245 | 0.684 | 0.003 |
| baseline_previous_gap | 3140 | 0.571 | 0.000 | 0.000 | 0.490 | 0.246 | 0.684 | 0.003 |
| baseline_us_overnight | 3140 | 0.653 | 0.576 | 0.728 | 0.654 | 0.220 | 0.632 | 0.007 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0409, t=6.11), `model_lightgbm`=yes (+0.0419, t=7.09)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.678 / 0.732 | 0.684 / 0.718 | 0.644 / 0.489 | 0.644 / 0.489 | 0.601 / 0.630 |
| vix_normal | 1901 | 0.699 / 0.755 | 0.715 / 0.756 | 0.577 / 0.493 | 0.577 / 0.485 | 0.670 / 0.671 |
| vix_high | 528 | 0.655 / 0.701 | 0.648 / 0.709 | 0.451 / 0.505 | 0.451 / 0.484 | 0.663 / 0.652 |
| is_expiry | 466 | 0.727 / 0.790 | 0.732 / 0.793 | 0.624 / 0.559 | 0.624 / 0.545 | 0.676 / 0.723 |
| not_is_expiry | 2674 | 0.680 / 0.740 | 0.690 / 0.739 | 0.561 / 0.490 | 0.561 / 0.486 | 0.649 / 0.646 |
| is_monthly_expiry | 154 | 0.714 / 0.759 | 0.721 / 0.778 | 0.695 / 0.556 | 0.695 / 0.523 | 0.649 / 0.687 |
| not_is_monthly_expiry | 2986 | 0.685 / 0.746 | 0.695 / 0.745 | 0.564 / 0.492 | 0.564 / 0.488 | 0.653 / 0.652 |
| is_rbi_policy | 25 | 0.880 / 0.849 | 0.800 / 0.849 | 0.720 / 0.746 | 0.720 / 0.575 | 0.680 / 0.734 |
| not_is_rbi_policy | 961 | 0.724 / 0.789 | 0.741 / 0.784 | 0.615 / 0.557 | 0.615 / 0.551 | 0.670 / 0.701 |
| is_union_budget | 15 | 0.333 / 0.500 | 0.467 / 0.589 | 0.467 / 0.643 | 0.467 / 0.536 | 0.467 / 0.536 |
| not_is_union_budget | 3125 | 0.688 / 0.749 | 0.698 / 0.747 | 0.571 / 0.494 | 0.571 / 0.490 | 0.654 / 0.655 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3137 | 0.687 / 0.748 | 0.697 / 0.747 | 0.571 / 0.495 | 0.571 / 0.490 | 0.653 / 0.655 |

## Gap down: nifty (morning run)

Out-of-sample 2014-01-29 to 2026-11-13: 3140 sessions, 50 walk-forward folds. Up-rate 0.184.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3140 | 0.837 | 0.646 | 0.250 | 0.782 | 0.120 | 0.396 | 0.019 |
| model_lightgbm | 3140 | 0.836 | 0.607 | 0.300 | 0.782 | 0.120 | 0.392 | 0.026 |
| baseline_base_rate | 3140 | 0.816 | 0.000 | 0.000 | 0.441 | 0.152 | 0.483 | 0.039 |
| baseline_previous_gap | 3140 | 0.816 | 0.000 | 0.000 | 0.469 | 0.152 | 0.483 | 0.030 |
| baseline_us_overnight | 3140 | 0.816 | 0.000 | 0.000 | 0.673 | 0.138 | 0.434 | 0.029 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0385, t=5.52), `model_lightgbm`=yes (+0.0428, t=7.00)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.869 / 0.769 | 0.866 / 0.765 | 0.851 / 0.433 | 0.851 / 0.454 | 0.851 / 0.651 |
| vix_normal | 1901 | 0.833 / 0.790 | 0.830 / 0.788 | 0.813 / 0.461 | 0.813 / 0.485 | 0.813 / 0.685 |
| vix_high | 528 | 0.807 / 0.767 | 0.814 / 0.769 | 0.780 / 0.389 | 0.780 / 0.413 | 0.780 / 0.659 |
| is_expiry | 466 | 0.822 / 0.807 | 0.848 / 0.809 | 0.788 / 0.469 | 0.788 / 0.480 | 0.788 / 0.698 |
| not_is_expiry | 2674 | 0.840 / 0.777 | 0.834 / 0.777 | 0.821 / 0.442 | 0.821 / 0.472 | 0.821 / 0.671 |
| is_monthly_expiry | 154 | 0.864 / 0.876 | 0.896 / 0.853 | 0.825 / 0.435 | 0.825 / 0.450 | 0.825 / 0.660 |
| not_is_monthly_expiry | 2986 | 0.836 / 0.778 | 0.833 / 0.779 | 0.816 / 0.441 | 0.816 / 0.470 | 0.816 / 0.674 |
| is_rbi_policy | 25 | 0.920 / 0.717 | 0.840 / 0.870 | 0.920 / 0.315 | 0.920 / 0.120 | 0.920 / 0.554 |
| not_is_rbi_policy | 961 | 0.824 / 0.801 | 0.839 / 0.807 | 0.786 / 0.424 | 0.786 / 0.473 | 0.786 / 0.677 |
| is_union_budget | 15 | 0.933 / 0.714 | 0.867 / 0.929 | 0.933 / 0.071 | 0.933 / 0.000 | 0.933 / 0.571 |
| not_is_union_budget | 3125 | 0.836 / 0.783 | 0.836 / 0.782 | 0.816 / 0.442 | 0.816 / 0.470 | 0.816 / 0.674 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3137 | 0.837 / 0.784 | 0.836 / 0.783 | 0.816 / 0.441 | 0.816 / 0.469 | 0.816 / 0.675 |

