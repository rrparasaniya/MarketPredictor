## Gap up: nifty (evening run)

Out-of-sample 2014-01-29 to 2026-11-27: 3149 sessions, 50 walk-forward folds. Up-rate 0.429.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3149 | 0.586 | 0.527 | 0.339 | 0.591 | 0.240 | 0.673 | 0.019 |
| model_lightgbm | 3149 | 0.579 | 0.514 | 0.343 | 0.583 | 0.240 | 0.673 | 0.016 |
| baseline_base_rate | 3149 | 0.571 | 0.000 | 0.000 | 0.495 | 0.245 | 0.684 | 0.003 |
| baseline_previous_gap | 3149 | 0.571 | 0.000 | 0.000 | 0.490 | 0.246 | 0.684 | 0.003 |
| baseline_us_overnight | 3149 | 0.571 | 0.000 | 0.000 | 0.519 | 0.245 | 0.683 | 0.013 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0096, t=2.58), `model_lightgbm`=yes (+0.0096, t=3.19)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 712 | 0.647 / 0.612 | 0.636 / 0.597 | 0.645 / 0.490 | 0.645 / 0.490 | 0.645 / 0.511 |
| vix_normal | 1909 | 0.583 / 0.569 | 0.577 / 0.563 | 0.576 / 0.493 | 0.576 / 0.485 | 0.576 / 0.513 |
| vix_high | 528 | 0.511 / 0.523 | 0.508 / 0.520 | 0.451 / 0.505 | 0.451 / 0.484 | 0.451 / 0.528 |
| is_expiry | 468 | 0.622 / 0.621 | 0.598 / 0.625 | 0.624 / 0.559 | 0.624 / 0.543 | 0.624 / 0.569 |
| not_is_expiry | 2681 | 0.579 / 0.584 | 0.576 / 0.577 | 0.561 / 0.490 | 0.561 / 0.487 | 0.561 / 0.514 |
| is_monthly_expiry | 155 | 0.665 / 0.572 | 0.632 / 0.611 | 0.690 / 0.555 | 0.690 / 0.520 | 0.690 / 0.555 |
| not_is_monthly_expiry | 2994 | 0.581 / 0.589 | 0.576 / 0.582 | 0.564 / 0.492 | 0.564 / 0.489 | 0.564 / 0.516 |
| is_rbi_policy | 25 | 0.720 / 0.698 | 0.720 / 0.683 | 0.720 / 0.746 | 0.720 / 0.575 | 0.720 / 0.627 |
| not_is_rbi_policy | 961 | 0.612 / 0.595 | 0.601 / 0.583 | 0.615 / 0.557 | 0.615 / 0.551 | 0.615 / 0.559 |
| is_union_budget | 15 | 0.600 / 0.554 | 0.600 / 0.643 | 0.467 / 0.643 | 0.467 / 0.536 | 0.467 / 0.571 |
| not_is_union_budget | 3134 | 0.586 / 0.591 | 0.579 / 0.583 | 0.571 / 0.494 | 0.571 / 0.490 | 0.571 / 0.518 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3146 | 0.586 / 0.591 | 0.579 / 0.583 | 0.571 / 0.495 | 0.571 / 0.490 | 0.571 / 0.519 |

## Gap down: nifty (evening run)

Out-of-sample 2014-01-29 to 2026-11-27: 3149 sessions, 50 walk-forward folds. Up-rate 0.184.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3149 | 0.815 | 0.167 | 0.002 | 0.574 | 0.150 | 0.477 | 0.024 |
| model_lightgbm | 3149 | 0.816 | 0.000 | 0.000 | 0.570 | 0.150 | 0.476 | 0.025 |
| baseline_base_rate | 3149 | 0.816 | 0.000 | 0.000 | 0.441 | 0.152 | 0.484 | 0.038 |
| baseline_previous_gap | 3149 | 0.816 | 0.000 | 0.000 | 0.468 | 0.152 | 0.483 | 0.030 |
| baseline_us_overnight | 3149 | 0.816 | 0.000 | 0.000 | 0.452 | 0.152 | 0.484 | 0.045 |

Best baseline (log loss): `baseline_previous_gap`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=no (+0.0065, t=1.73), `model_lightgbm`=yes (+0.0076, t=2.32)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 712 | 0.850 / 0.616 | 0.850 / 0.586 | 0.850 / 0.435 | 0.850 / 0.456 | 0.850 / 0.420 |
| vix_normal | 1909 | 0.814 / 0.566 | 0.814 / 0.558 | 0.814 / 0.460 | 0.814 / 0.484 | 0.814 / 0.473 |
| vix_high | 528 | 0.773 / 0.546 | 0.780 / 0.555 | 0.780 / 0.389 | 0.780 / 0.413 | 0.780 / 0.403 |
| is_expiry | 468 | 0.786 / 0.581 | 0.788 / 0.577 | 0.788 / 0.468 | 0.788 / 0.478 | 0.788 / 0.453 |
| not_is_expiry | 2681 | 0.820 / 0.570 | 0.821 / 0.567 | 0.821 / 0.442 | 0.821 / 0.472 | 0.821 / 0.456 |
| is_monthly_expiry | 155 | 0.826 / 0.617 | 0.826 / 0.592 | 0.826 / 0.435 | 0.826 / 0.448 | 0.826 / 0.440 |
| not_is_monthly_expiry | 2994 | 0.814 / 0.572 | 0.816 / 0.569 | 0.816 / 0.441 | 0.816 / 0.470 | 0.816 / 0.453 |
| is_rbi_policy | 25 | 0.920 / 0.304 | 0.920 / 0.587 | 0.920 / 0.315 | 0.920 / 0.120 | 0.920 / 0.489 |
| not_is_rbi_policy | 961 | 0.785 / 0.569 | 0.786 / 0.573 | 0.786 / 0.424 | 0.786 / 0.473 | 0.786 / 0.439 |
| is_union_budget | 15 | 0.933 / 0.000 | 0.933 / 0.357 | 0.933 / 0.071 | 0.933 / 0.000 | 0.933 / 0.000 |
| not_is_union_budget | 3134 | 0.814 / 0.573 | 0.816 / 0.570 | 0.816 / 0.442 | 0.816 / 0.469 | 0.816 / 0.453 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3146 | 0.815 / 0.575 | 0.816 / 0.570 | 0.816 / 0.441 | 0.816 / 0.469 | 0.816 / 0.453 |

### Warnings

- model_logistic: does not clearly beat the best baseline (baseline_previous_gap): log-loss gain +0.0065, t=1.73 (needs > 0 and t >= 2.0).

