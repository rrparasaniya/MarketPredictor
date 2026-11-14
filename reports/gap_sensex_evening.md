## Gap up: sensex (evening run)

Out-of-sample 2014-01-20 to 2026-11-13: 3145 sessions, 50 walk-forward folds. Up-rate 0.438.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3145 | 0.591 | 0.541 | 0.432 | 0.608 | 0.238 | 0.670 | 0.021 |
| model_lightgbm | 3145 | 0.587 | 0.534 | 0.443 | 0.612 | 0.237 | 0.667 | 0.029 |
| baseline_base_rate | 3145 | 0.562 | 0.000 | 0.000 | 0.493 | 0.247 | 0.686 | 0.002 |
| baseline_previous_gap | 3145 | 0.562 | 0.000 | 0.000 | 0.497 | 0.247 | 0.686 | 0.002 |
| baseline_us_overnight | 3145 | 0.562 | 0.000 | 0.000 | 0.520 | 0.246 | 0.685 | 0.005 |

Best baseline (log loss): `baseline_us_overnight`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0152, t=3.71), `model_lightgbm`=yes (+0.0176, t=4.28)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.646 / 0.600 | 0.650 / 0.619 | 0.650 / 0.462 | 0.650 / 0.473 | 0.650 / 0.506 |
| vix_normal | 1907 | 0.586 / 0.592 | 0.567 / 0.588 | 0.568 / 0.487 | 0.568 / 0.489 | 0.568 / 0.508 |
| vix_high | 527 | 0.535 / 0.520 | 0.573 / 0.537 | 0.425 / 0.506 | 0.425 / 0.484 | 0.425 / 0.541 |
| is_expiry | 294 | 0.629 / 0.594 | 0.605 / 0.633 | 0.622 / 0.554 | 0.622 / 0.555 | 0.622 / 0.556 |
| not_is_expiry | 2851 | 0.587 / 0.607 | 0.585 / 0.609 | 0.556 / 0.489 | 0.556 / 0.493 | 0.556 / 0.518 |
| is_monthly_expiry | 154 | 0.591 / 0.564 | 0.584 / 0.616 | 0.617 / 0.612 | 0.617 / 0.609 | 0.617 / 0.589 |
| not_is_monthly_expiry | 2991 | 0.591 / 0.609 | 0.587 / 0.612 | 0.560 / 0.488 | 0.560 / 0.491 | 0.560 / 0.517 |
| is_rbi_policy | 25 | 0.600 / 0.674 | 0.720 / 0.708 | 0.640 / 0.750 | 0.640 / 0.660 | 0.640 / 0.708 |
| not_is_rbi_policy | 959 | 0.638 / 0.626 | 0.627 / 0.622 | 0.636 / 0.553 | 0.636 / 0.560 | 0.636 / 0.576 |
| is_union_budget | 14 | 0.714 / 0.455 | 0.357 / 0.515 | 0.214 / 0.545 | 0.214 / 0.636 | 0.214 / 0.667 |
| not_is_union_budget | 3131 | 0.591 / 0.606 | 0.588 / 0.612 | 0.564 / 0.493 | 0.564 / 0.497 | 0.564 / 0.520 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3142 | 0.591 / 0.608 | 0.587 / 0.612 | 0.563 / 0.494 | 0.563 / 0.497 | 0.563 / 0.521 |

## Gap down: sensex (evening run)

Out-of-sample 2014-01-20 to 2026-11-13: 3145 sessions, 50 walk-forward folds. Up-rate 0.149.

| model | n | accuracy | precision | recall | roc_auc | brier | log_loss | ece |
|---|---|---|---|---|---|---|---|---|
| model_logistic | 3145 | 0.848 | 0.286 | 0.013 | 0.633 | 0.125 | 0.413 | 0.027 |
| model_lightgbm | 3145 | 0.851 | 0.250 | 0.002 | 0.626 | 0.126 | 0.415 | 0.035 |
| baseline_base_rate | 3145 | 0.851 | 0.000 | 0.000 | 0.469 | 0.128 | 0.425 | 0.006 |
| baseline_previous_gap | 3145 | 0.851 | 0.000 | 0.000 | 0.484 | 0.128 | 0.424 | 0.007 |
| baseline_us_overnight | 3145 | 0.851 | 0.000 | 0.000 | 0.465 | 0.128 | 0.425 | 0.006 |

Best baseline (log loss): `baseline_previous_gap`. Clearly beats it (paired log-loss gain, t-stat): `model_logistic`=yes (+0.0118, t=2.57), `model_lightgbm`=yes (+0.0092, t=2.01)

### Accuracy / ROC-AUC by regime and event

| subset | n | model_logistic | model_lightgbm | baseline_base_rate | baseline_previous_gap | baseline_us_overnight |
|---|---|---|---|---|---|---|
| vix_low | 711 | 0.866 / 0.665 | 0.866 / 0.616 | 0.866 / 0.558 | 0.866 / 0.556 | 0.866 / 0.519 |
| vix_normal | 1907 | 0.858 / 0.633 | 0.858 / 0.624 | 0.858 / 0.480 | 0.858 / 0.485 | 0.858 / 0.478 |
| vix_high | 527 | 0.789 / 0.594 | 0.801 / 0.608 | 0.805 / 0.429 | 0.805 / 0.446 | 0.805 / 0.420 |
| is_expiry | 294 | 0.820 / 0.634 | 0.820 / 0.570 | 0.823 / 0.522 | 0.823 / 0.513 | 0.823 / 0.494 |
| not_is_expiry | 2851 | 0.851 / 0.630 | 0.854 / 0.628 | 0.854 / 0.463 | 0.854 / 0.481 | 0.854 / 0.461 |
| is_monthly_expiry | 154 | 0.857 / 0.638 | 0.864 / 0.607 | 0.864 / 0.490 | 0.864 / 0.474 | 0.864 / 0.469 |
| not_is_monthly_expiry | 2991 | 0.848 / 0.633 | 0.850 / 0.626 | 0.851 / 0.468 | 0.851 / 0.485 | 0.851 / 0.464 |
| is_rbi_policy | 25 | 0.960 / 0.292 | 0.960 / 0.958 | 0.960 / 0.188 | 0.960 / 0.062 | 0.960 / 0.104 |
| not_is_rbi_policy | 959 | 0.790 / 0.529 | 0.790 / 0.515 | 0.792 / 0.390 | 0.792 / 0.450 | 0.792 / 0.387 |
| is_union_budget | 14 | 0.929 / 0.231 | 0.929 / 0.231 | 0.929 / 0.000 | 0.929 / 0.000 | 0.929 / 0.000 |
| not_is_union_budget | 3131 | 0.848 / 0.634 | 0.850 / 0.627 | 0.851 / 0.470 | 0.851 / 0.486 | 0.851 / 0.466 |
| is_election_results | 3 | — | — | — | — | — |
| not_is_election_results | 3142 | 0.849 / 0.634 | 0.851 / 0.625 | 0.851 / 0.469 | 0.851 / 0.485 | 0.851 / 0.465 |

