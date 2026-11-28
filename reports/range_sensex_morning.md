## Range: sensex (morning run)

Out-of-sample 2014-01-20 to 2026-11-27: 3154 sessions, 26 walk-forward folds. Widths are average band width in % of price; nominal coverage is the band level.

### open  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3154 | 0.650 | 0.941 | 0.59 | 1.56 | 0.826 | 0.18 |
| baseline_vix_normal | 3154 | 0.958 | 0.994 | 2.08 | 4.10 | 1.304 | 0.25 |
| baseline_vix_empirical | 3154 | 0.635 | 0.930 | 0.62 | 1.66 | 0.964 | 0.20 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.606 / 0.952 | 0.930 / 0.999 |
| vix_normal | 1916 | 0.669 / 0.966 | 0.947 / 0.992 |
| vix_high | 527 | 0.639 / 0.939 | 0.935 / 0.994 |
| is_expiry | 296 | 0.645 / 0.959 | 0.946 / 0.990 |
| not_is_expiry | 2858 | 0.650 / 0.958 | 0.941 / 0.994 |
| is_monthly_expiry | 155 | 0.723 / 0.981 | 0.968 / 0.994 |
| not_is_monthly_expiry | 2999 | 0.646 / 0.957 | 0.940 / 0.994 |
| is_rbi_policy | 25 | 0.840 / 1.000 | 1.000 / 1.000 |
| not_is_rbi_policy | 959 | 0.651 / 0.947 | 0.943 / 0.993 |
| not_is_union_budget | 3140 | 0.650 / 0.959 | 0.941 / 0.994 |
| not_is_election_results | 3151 | 0.651 / 0.958 | 0.941 / 0.994 |

### high  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3154 | 0.674 | 0.945 | 0.97 | 2.30 | 1.134 | 0.28 |
| baseline_vix_normal | 3154 | 0.793 | 0.981 | 2.08 | 4.10 | 1.779 | 0.55 |
| baseline_vix_empirical | 3154 | 0.673 | 0.947 | 1.02 | 2.44 | 1.239 | 0.32 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.641 / 0.795 | 0.955 / 0.985 |
| vix_normal | 1916 | 0.685 / 0.804 | 0.944 / 0.981 |
| vix_high | 527 | 0.677 / 0.748 | 0.935 / 0.975 |
| is_expiry | 296 | 0.622 / 0.736 | 0.916 / 0.959 |
| not_is_expiry | 2858 | 0.679 / 0.798 | 0.948 / 0.983 |
| is_monthly_expiry | 155 | 0.626 / 0.755 | 0.935 / 0.974 |
| not_is_monthly_expiry | 2999 | 0.677 / 0.795 | 0.945 / 0.981 |
| is_rbi_policy | 25 | 0.840 / 0.800 | 0.960 / 0.960 |
| not_is_rbi_policy | 959 | 0.633 / 0.797 | 0.941 / 0.977 |
| not_is_union_budget | 3140 | 0.675 / 0.794 | 0.945 / 0.981 |
| not_is_election_results | 3151 | 0.675 / 0.793 | 0.945 / 0.981 |

### low  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3154 | 0.677 | 0.946 | 1.16 | 2.62 | 1.362 | 0.36 |
| baseline_vix_normal | 3154 | 0.808 | 0.967 | 2.08 | 4.10 | 1.837 | 0.45 |
| baseline_vix_empirical | 3154 | 0.663 | 0.946 | 1.21 | 2.73 | 1.474 | 0.39 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.660 / 0.807 | 0.947 / 0.976 |
| vix_normal | 1916 | 0.678 / 0.804 | 0.945 / 0.965 |
| vix_high | 527 | 0.696 / 0.820 | 0.949 / 0.964 |
| is_expiry | 296 | 0.628 / 0.784 | 0.922 / 0.963 |
| not_is_expiry | 2858 | 0.682 / 0.810 | 0.948 / 0.968 |
| is_monthly_expiry | 155 | 0.658 / 0.781 | 0.948 / 0.961 |
| not_is_monthly_expiry | 2999 | 0.678 / 0.809 | 0.946 / 0.968 |
| is_rbi_policy | 25 | 0.840 / 0.880 | 1.000 / 0.960 |
| not_is_rbi_policy | 959 | 0.681 / 0.801 | 0.956 / 0.974 |
| not_is_union_budget | 3140 | 0.679 / 0.809 | 0.946 / 0.968 |
| not_is_election_results | 3151 | 0.678 / 0.808 | 0.946 / 0.968 |

