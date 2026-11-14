## Range: sensex (morning run)

Out-of-sample 2014-01-20 to 2026-11-13: 3145 sessions, 25 walk-forward folds. Widths are average band width in % of price; nominal coverage is the band level.

### open  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3145 | 0.650 | 0.941 | 0.59 | 1.56 | 0.825 | 0.18 |
| baseline_vix_normal | 3145 | 0.959 | 0.994 | 2.08 | 4.10 | 1.305 | 0.25 |
| baseline_vix_empirical | 3145 | 0.635 | 0.930 | 0.62 | 1.66 | 0.964 | 0.20 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.606 / 0.952 | 0.930 / 0.999 |
| vix_normal | 1907 | 0.669 / 0.966 | 0.947 / 0.992 |
| vix_high | 527 | 0.639 / 0.939 | 0.935 / 0.994 |
| is_expiry | 294 | 0.643 / 0.959 | 0.946 / 0.990 |
| not_is_expiry | 2851 | 0.650 / 0.959 | 0.941 / 0.994 |
| is_monthly_expiry | 154 | 0.721 / 0.981 | 0.968 / 0.994 |
| not_is_monthly_expiry | 2991 | 0.646 / 0.958 | 0.940 / 0.994 |
| is_rbi_policy | 25 | 0.840 / 1.000 | 1.000 / 1.000 |
| not_is_rbi_policy | 959 | 0.651 / 0.947 | 0.943 / 0.993 |
| not_is_union_budget | 3131 | 0.650 / 0.959 | 0.941 / 0.994 |
| not_is_election_results | 3142 | 0.650 / 0.959 | 0.941 / 0.994 |

### high  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3145 | 0.675 | 0.945 | 0.97 | 2.30 | 1.132 | 0.28 |
| baseline_vix_normal | 3145 | 0.793 | 0.981 | 2.08 | 4.10 | 1.778 | 0.54 |
| baseline_vix_empirical | 3145 | 0.674 | 0.948 | 1.02 | 2.44 | 1.238 | 0.32 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.641 / 0.795 | 0.955 / 0.985 |
| vix_normal | 1907 | 0.686 / 0.805 | 0.944 / 0.981 |
| vix_high | 527 | 0.677 / 0.748 | 0.935 / 0.975 |
| is_expiry | 294 | 0.622 / 0.738 | 0.915 / 0.959 |
| not_is_expiry | 2851 | 0.680 / 0.799 | 0.948 / 0.983 |
| is_monthly_expiry | 154 | 0.623 / 0.753 | 0.935 / 0.974 |
| not_is_monthly_expiry | 2991 | 0.677 / 0.795 | 0.946 / 0.981 |
| is_rbi_policy | 25 | 0.840 / 0.800 | 0.960 / 0.960 |
| not_is_rbi_policy | 959 | 0.633 / 0.797 | 0.941 / 0.977 |
| not_is_union_budget | 3131 | 0.676 / 0.794 | 0.945 / 0.981 |
| not_is_election_results | 3142 | 0.675 / 0.793 | 0.945 / 0.981 |

### low  (shown: ML model)

| source | n | cov68 | cov95 | width68% | width95% | pinball×1e3 | med abs err% |
|---|---|---|---|---|---|---|---|
| model | 3145 | 0.678 | 0.946 | 1.16 | 2.62 | 1.361 | 0.36 |
| baseline_vix_normal | 3145 | 0.808 | 0.967 | 2.08 | 4.10 | 1.836 | 0.45 |
| baseline_vix_empirical | 3145 | 0.663 | 0.946 | 1.21 | 2.73 | 1.473 | 0.39 |

Coverage by subset (model / VIX baseline):

| subset | n | cov68 | cov95 |
|---|---|---|---|
| vix_low | 711 | 0.660 / 0.807 | 0.947 / 0.976 |
| vix_normal | 1907 | 0.679 / 0.805 | 0.945 / 0.965 |
| vix_high | 527 | 0.696 / 0.820 | 0.949 / 0.964 |
| is_expiry | 294 | 0.626 / 0.782 | 0.922 / 0.963 |
| not_is_expiry | 2851 | 0.683 / 0.811 | 0.948 / 0.968 |
| is_monthly_expiry | 154 | 0.656 / 0.779 | 0.948 / 0.961 |
| not_is_monthly_expiry | 2991 | 0.679 / 0.809 | 0.946 / 0.968 |
| is_rbi_policy | 25 | 0.840 / 0.880 | 1.000 / 0.960 |
| not_is_rbi_policy | 959 | 0.681 / 0.801 | 0.956 / 0.974 |
| not_is_union_budget | 3131 | 0.679 / 0.809 | 0.946 / 0.968 |
| not_is_election_results | 3142 | 0.678 / 0.808 | 0.946 / 0.968 |

