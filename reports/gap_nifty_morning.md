## Gap up: nifty (morning run)

Out-of-sample 2014-01-29 to 2026-11-27: 3149 sessions, 50 walk-forward folds. Up-rate 0.429.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3149 | 0.686 | 0.638 | 0.621 | 0.747 | 0.202 | 0.591 | 0.032 |
| model_lightgbm | 3149 | 0.696 | 0.655 | 0.617 | 0.745 | 0.202 | 0.590 | 0.028 |
| baseline_base_rate | 3149 | 0.571 | 0.000 | 0.000 | 0.495 | 0.245 | 0.684 | 0.003 |
| baseline_previous_gap | 3149 | 0.571 | 0.000 | 0.000 | 0.490 | 0.246 | 0.684 | 0.003 |
| baseline_us_overnight | 3149 | 0.653 | 0.576 | 0.726 | 0.653 | 0.220 | 0.632 | 0.008 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0406, t=6.07), `model_lightgbm`=yes (+0.0418, t=7.09)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.678 / 0.732 | 0.684 / 0.718 | 0.644 / 0.489 | 0.644 / 0.489 | 0.601 / 0.630 |
| vix_normal | 1910 | 0.698 / 0.754 | 0.714 / 0.755 | 0.576 / 0.493 | 0.576 / 0.485 | 0.669 / 0.670 |
| vix_high | 528 | 0.655 / 0.701 | 0.648 / 0.709 | 0.451 / 0.505 | 0.451 / 0.484 | 0.663 / 0.652 |
| is_expiry | 468 | 0.726 / 0.786 | 0.731 / 0.790 | 0.624 / 0.559 | 0.624 / 0.543 | 0.675 / 0.721 |
| not_is_expiry | 2681 | 0.679 / 0.739 | 0.690 / 0.739 | 0.561 / 0.490 | 0.561 / 0.487 | 0.649 / 0.646 |
| is_monthly_expiry | 155 | 0.710 / 0.744 | 0.716 / 0.765 | 0.690 / 0.555 | 0.690 / 0.520 | 0.645 / 0.678 |
| not_is_monthly_expiry | 2994 | 0.685 / 0.746 | 0.695 / 0.745 | 0.564 / 0.492 | 0.564 / 0.489 | 0.653 / 0.652 |
| is_rbi_policy | 25 | 0.880 / 0.849 | 0.800 / 0.849 | 0.720 / 0.746 | 0.720 / 0.575 | 0.680 / 0.734 |
| not_is_rbi_policy | 961 | 0.724 / 0.789 | 0.741 / 0.784 | 0.615 / 0.557 | 0.615 / 0.551 | 0.670 / 0.701 |
| is_union_budget | 15 | 0.333 / 0.500 | 0.467 / 0.589 | 0.467 / 0.643 | 0.467 / 0.536 | 0.467 / 0.536 |
| not_is_union_budget | 3134 | 0.688 / 0.748 | 0.697 / 0.746 | 0.571 / 0.494 | 0.571 / 0.490 | 0.653 / 0.654 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3146 | 0.687 / 0.747 | 0.697 / 0.746 | 0.571 / 0.495 | 0.571 / 0.490 | 0.653 / 0.655 |

## Gap down: nifty (morning run)

Out-of-sample 2014-01-29 to 2026-11-27: 3149 sessions, 50 walk-forward folds. Up-rate 0.184.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3149 | 0.836 | 0.643 | 0.249 | 0.782 | 0.121 | 0.396 | 0.020 |
| model_lightgbm | 3149 | 0.835 | 0.603 | 0.299 | 0.782 | 0.120 | 0.392 | 0.026 |
| baseline_base_rate | 3149 | 0.816 | 0.000 | 0.000 | 0.441 | 0.152 | 0.484 | 0.038 |
| baseline_previous_gap | 3149 | 0.816 | 0.000 | 0.000 | 0.468 | 0.152 | 0.483 | 0.030 |
| baseline_us_overnight | 3149 | 0.816 | 0.000 | 0.000 | 0.673 | 0.138 | 0.435 | 0.030 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0384, t=5.52), `model_lightgbm`=yes (+0.0427, t=7.00)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.869 / 0.769 | 0.866 / 0.765 | 0.851 / 0.433 | 0.851 / 0.454 | 0.851 / 0.651 |
| vix_normal | 1910 | 0.832 / 0.789 | 0.829 / 0.787 | 0.813 / 0.461 | 0.813 / 0.484 | 0.813 / 0.685 |
| vix_high | 528 | 0.807 / 0.767 | 0.814 / 0.769 | 0.780 / 0.389 | 0.780 / 0.413 | 0.780 / 0.659 |
| is_expiry | 468 | 0.821 / 0.805 | 0.844 / 0.806 | 0.788 / 0.468 | 0.788 / 0.478 | 0.788 / 0.695 |
| not_is_expiry | 2681 | 0.839 / 0.777 | 0.833 / 0.777 | 0.821 / 0.442 | 0.821 / 0.472 | 0.821 / 0.671 |
| is_monthly_expiry | 155 | 0.858 / 0.871 | 0.890 / 0.849 | 0.826 / 0.435 | 0.826 / 0.448 | 0.826 / 0.657 |
| not_is_monthly_expiry | 2994 | 0.835 / 0.778 | 0.832 / 0.779 | 0.816 / 0.441 | 0.816 / 0.470 | 0.816 / 0.674 |
| is_rbi_policy | 25 | 0.920 / 0.717 | 0.840 / 0.870 | 0.920 / 0.315 | 0.920 / 0.120 | 0.920 / 0.554 |
| not_is_rbi_policy | 961 | 0.824 / 0.801 | 0.839 / 0.807 | 0.786 / 0.424 | 0.786 / 0.473 | 0.786 / 0.677 |
| is_union_budget | 15 | 0.933 / 0.714 | 0.867 / 0.929 | 0.933 / 0.071 | 0.933 / 0.000 | 0.933 / 0.571 |
| not_is_union_budget | 3134 | 0.836 / 0.782 | 0.835 / 0.782 | 0.816 / 0.442 | 0.816 / 0.469 | 0.816 / 0.673 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3146 | 0.837 / 0.783 | 0.835 / 0.783 | 0.816 / 0.441 | 0.816 / 0.469 | 0.816 / 0.674 |

