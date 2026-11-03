# MarketPredictor

Next-session forecasts for NIFTY 50 and SENSEX: opening gap, open/high/low range (68% and 95%
bands), and direction. See `CLAUDE.md` for the design rules and `reports/` (generated) for
walk-forward results.

> For educational purposes only. Not investment advice. Not SEBI-registered.

## Run locally

```bash
pip install -r requirements.txt
python scripts/daily_update.py      # fetch data + generate prediction
python scripts/retrain.py           # retrain all models walk-forward (writes reports/)
python scripts/backtest.py          # backtest the walk-forward forecasts after costs
streamlit run app/main.py           # launch dashboard
pytest tests/                       # run tests
```

## Hosting on Streamlit Community Cloud

The deployed app runs from the **`live`** branch: the code from `master` plus the
generated data, trained models and predictions log. A GitHub Action
(`.github/workflows/update.yml`) rebuilds `live` on a schedule:

| When (IST) | What |
|---|---|
| Weekdays 08:15 | Morning forecast for today's session |
| Weekdays 16:30 | Evening forecast for the next session |
| Saturdays 10:00 | Retrain all models and rerun the backtest |

Streamlit Cloud picks up each push to `live` automatically. Scheduled workflows only run
from the default branch, so the schedule starts once the workflow file is on `master`.
You can also start a run from the repo's **Actions** tab → *Update forecasts* → *Run workflow*.

### One-time setup

1. Go to <https://share.streamlit.io> and sign in with GitHub.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Repository `rrparasaniya/MarketPredictor`, branch **`live`**, main file path **`app/main.py`**.
4. Under **Advanced settings**, choose Python **3.12**.
5. Click **Deploy**. The first build takes a few minutes while it installs the dependencies.
