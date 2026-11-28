## Range: sensex (evening run)

Out-of-sample 2014-01-20 to 2026-11-27: 3154 sessions, 26 walk-forward folds. Widths are average band width in % of price; nominal coverage is the band level.

### open  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3154 | 0.658 | 0.945 | 0.67 | 1.79 | 0.945 | 0.21 |
| baseline_vix_normal | 3154 | 0.958 | 0.994 | 2.08 | 4.10 | 1.304 | 0.25 |
| baseline_vix_empirical | 3154 | 0.635 | 0.930 | 0.62 | 1.66 | 0.964 | 0.20 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.650 / 0.952 | 0.952 / 0.999 |
| vix_normal | 1916 | 0.674 / 0.966 | 0.946 / 0.992 |
| vix_high | 527 | 0.607 / 0.939 | 0.935 / 0.994 |
| is_expiry | 296 | 0.652 / 0.959 | 0.953 / 0.990 |
| not_is_expiry | 2858 | 0.658 / 0.958 | 0.945 / 0.994 |
| is_monthly_expiry | 155 | 0.703 / 0.981 | 0.961 / 0.994 |
| not_is_monthly_expiry | 2999 | 0.655 / 0.957 | 0.945 / 0.994 |
| is_rbi_policy | 25 | 0.880 / 1.000 | 1.000 / 1.000 |
| not_is_rbi_policy | 959 | 0.690 / 0.947 | 0.946 / 0.993 |
| not_is_union_budget | 3140 | 0.657 / 0.959 | 0.946 / 0.994 |
| not_is_election_results | 3151 | 0.658 / 0.958 | 0.945 / 0.994 |

### high  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3154 | 0.671 | 0.950 | 1.02 | 2.51 | 1.233 | 0.32 |
| baseline_vix_normal | 3154 | 0.793 | 0.981 | 2.08 | 4.10 | 1.779 | 0.55 |
| baseline_vix_empirical | 3154 | 0.673 | 0.947 | 1.02 | 2.44 | 1.239 | 0.32 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.667 / 0.795 | 0.954 / 0.985 |
| vix_normal | 1916 | 0.681 / 0.804 | 0.951 / 0.981 |
| vix_high | 527 | 0.638 / 0.750 | 0.941 / 0.975 |
| is_expiry | 296 | 0.625 / 0.736 | 0.926 / 0.959 |
| not_is_expiry | 2858 | 0.675 / 0.799 | 0.953 / 0.983 |
| is_monthly_expiry | 155 | 0.639 / 0.755 | 0.942 / 0.974 |
| not_is_monthly_expiry | 2999 | 0.672 / 0.795 | 0.951 / 0.981 |
| is_rbi_policy | 25 | 0.760 / 0.800 | 0.960 / 0.960 |
| not_is_rbi_policy | 959 | 0.659 / 0.797 | 0.949 / 0.977 |
| not_is_union_budget | 3140 | 0.672 / 0.794 | 0.951 / 0.981 |
| not_is_election_results | 3151 | 0.671 / 0.793 | 0.950 / 0.981 |

### low  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3154 | 0.684 | 0.944 | 1.28 | 2.75 | 1.463 | 0.39 |
| baseline_vix_normal | 3154 | 0.808 | 0.967 | 2.08 | 4.10 | 1.837 | 0.45 |
| baseline_vix_empirical | 3154 | 0.663 | 0.946 | 1.21 | 2.73 | 1.474 | 0.39 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.681 / 0.807 | 0.954 / 0.976 |
| vix_normal | 1916 | 0.688 / 0.804 | 0.943 / 0.965 |
| vix_high | 527 | 0.674 / 0.820 | 0.937 / 0.964 |
| is_expiry | 296 | 0.662 / 0.784 | 0.926 / 0.963 |
| not_is_expiry | 2858 | 0.686 / 0.810 | 0.946 / 0.968 |
| is_monthly_expiry | 155 | 0.684 / 0.781 | 0.923 / 0.961 |
| not_is_monthly_expiry | 2999 | 0.684 / 0.809 | 0.945 / 0.968 |
| is_rbi_policy | 25 | 0.920 / 0.880 | 1.000 / 0.960 |
| not_is_rbi_policy | 959 | 0.704 / 0.801 | 0.957 / 0.974 |
| not_is_union_budget | 3140 | 0.685 / 0.809 | 0.945 / 0.968 |
| not_is_election_results | 3151 | 0.684 / 0.808 | 0.944 / 0.968 |

