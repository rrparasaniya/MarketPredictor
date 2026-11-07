## Range: nifty (evening run)

Out-of-sample 2014-01-29 to 2026-11-06: 3136 sessions, 25 walk-forward folds. Widths are average band width in % of price; nominal coverage is the band level.

### open  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3136 | 0.670 | 0.945 | 0.79 | 1.96 | 1.019 | 0.24 |
| baseline_vix_normal | 3136 | 0.955 | 0.993 | 2.08 | 4.10 | 1.332 | 0.27 |
| baseline_vix_empirical | 3136 | 0.662 | 0.945 | 0.75 | 1.92 | 1.033 | 0.23 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 712 | 0.667 / 0.956 | 0.955 / 0.999 |
| vix_normal | 1896 | 0.687 / 0.960 | 0.947 / 0.993 |
| vix_high | 528 | 0.612 / 0.932 | 0.926 / 0.985 |
| is_expiry | 465 | 0.671 / 0.963 | 0.961 / 0.991 |
| not_is_expiry | 2671 | 0.669 / 0.953 | 0.943 / 0.993 |
| is_monthly_expiry | 154 | 0.734 / 0.974 | 0.987 / 0.994 |
| not_is_monthly_expiry | 2982 | 0.666 / 0.954 | 0.943 / 0.993 |
| is_rbi_policy | 25 | 0.920 / 1.000 | 1.000 / 1.000 |
| not_is_rbi_policy | 961 | 0.712 / 0.950 | 0.951 / 0.995 |
| not_is_union_budget | 3121 | 0.670 / 0.955 | 0.946 / 0.993 |
| not_is_election_results | 3133 | 0.670 / 0.955 | 0.945 / 0.993 |

### high  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3136 | 0.684 | 0.952 | 1.05 | 2.53 | 1.239 | 0.31 |
| baseline_vix_normal | 3136 | 0.799 | 0.983 | 2.08 | 4.10 | 1.758 | 0.53 |
| baseline_vix_empirical | 3136 | 0.685 | 0.951 | 1.06 | 2.52 | 1.248 | 0.31 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 712 | 0.684 / 0.809 | 0.955 / 0.986 |
| vix_normal | 1896 | 0.690 / 0.809 | 0.953 / 0.984 |
| vix_high | 528 | 0.663 / 0.754 | 0.941 / 0.975 |
| is_expiry | 465 | 0.665 / 0.815 | 0.961 / 0.987 |
| not_is_expiry | 2671 | 0.688 / 0.797 | 0.950 / 0.982 |
| is_monthly_expiry | 154 | 0.656 / 0.818 | 0.968 / 0.987 |
| not_is_monthly_expiry | 2982 | 0.686 / 0.798 | 0.951 / 0.983 |
| is_rbi_policy | 25 | 0.760 / 0.800 | 0.960 / 0.960 |
| not_is_rbi_policy | 961 | 0.669 / 0.797 | 0.955 / 0.980 |
| not_is_union_budget | 3121 | 0.686 / 0.801 | 0.952 / 0.983 |
| not_is_election_results | 3133 | 0.685 / 0.800 | 0.952 / 0.983 |

### low  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3136 | 0.685 | 0.948 | 1.31 | 2.83 | 1.472 | 0.38 |
| baseline_vix_normal | 3136 | 0.803 | 0.964 | 2.08 | 4.10 | 1.851 | 0.45 |
| baseline_vix_empirical | 3136 | 0.664 | 0.946 | 1.25 | 2.83 | 1.483 | 0.39 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 712 | 0.691 / 0.812 | 0.961 / 0.976 |
| vix_normal | 1896 | 0.688 / 0.796 | 0.943 / 0.960 |
| vix_high | 528 | 0.669 / 0.816 | 0.949 / 0.962 |
| is_expiry | 465 | 0.720 / 0.794 | 0.957 / 0.968 |
| not_is_expiry | 2671 | 0.679 / 0.805 | 0.946 / 0.964 |
| is_monthly_expiry | 154 | 0.708 / 0.779 | 0.935 / 0.955 |
| not_is_monthly_expiry | 2982 | 0.684 / 0.804 | 0.949 / 0.965 |
| is_rbi_policy | 25 | 0.880 / 0.880 | 1.000 / 0.960 |
| not_is_rbi_policy | 961 | 0.701 / 0.800 | 0.957 / 0.973 |
| not_is_union_budget | 3121 | 0.686 / 0.804 | 0.949 / 0.965 |
| not_is_election_results | 3133 | 0.685 / 0.803 | 0.948 / 0.965 |

