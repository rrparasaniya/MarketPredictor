# Optional inputs

Drop CSV files here to add extra features. If a file is missing, the pipeline skips it.
Paths and release times are set under `optional_inputs` in `config.yaml`.

| File | Contents | Default `available_time` (IST) |
|---|---|---|
| `fii_dii.csv` | FII/DII net cash flows (₹ crore) | 20:00 on that date |
| `gift_nifty.csv` | GIFT Nifty morning level in a `price` column (used as a premium vs the previous index close) | 08:30 on that date |
| `pcr_oi.csv` | Put-call ratio, open interest | 18:00 on that date |

Format: a `date` column (YYYY-MM-DD, IST session date) plus any numeric columns.
To override the release time row by row, add an `available_at` column with a timezone
offset, e.g. `2026-11-03T19:45:00+05:30`. Rows are only used after `available_at`.
