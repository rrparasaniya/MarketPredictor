# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project overview
Prediction app for NIFTY 50 (^NSEI) and SENSEX (^BSESN). It predicts ONLY the next single trading session:
1. **Direction**: probability the close is above the previous close × (1 + threshold)
2. **Gap**: gap-up / gap-down / flat open
3. **Range**: next session's open, high, and low, with 68% and 95% bands

No multi-day or weekly predictions. Educational tool only, not investment advice.

## Prediction timing (Asia/Kolkata)
- Before 9:15 AM IST → predict TODAY (previous close + overnight cues)
- After 3:30 PM IST → predict the NEXT trading session (skip weekends and NSE holidays)
- 9:15 AM–3:30 PM IST → show the latest prediction for today, don't make a new one
- Scheduled runs: ~8:45 AM IST and after 3:30 PM IST

## Tech stack
Python 3.11+, pandas, numpy, scikit-learn, xgboost, lightgbm, yfinance, shap, Streamlit, pytest.
All settings live in `config.yaml`. Never hardcode thresholds, costs, dates, or expiry days.

## Project structure
```
config.yaml
data/        # downloaders, NSE holiday calendar, raw/processed cache
features/    # feature engineering (technical, global cues, events)
models/      # direction, gap, range (quantile) models + saved artifacts
backtest/    # walk-forward evaluation, cost model, metrics
app/         # Streamlit dashboard
tests/       # leakage tests, unit tests
scripts/     # daily_update.py, retrain.py
```

## Commands
```bash
pip install -r requirements.txt
python scripts/daily_update.py      # fetch data + generate prediction
python scripts/retrain.py           # retrain all models walk-forward
streamlit run app/main.py           # launch dashboard
pytest tests/                       # run tests (must pass before any commit)
```

## Data sources (yfinance, keep swappable behind one interface)
- Indices: ^NSEI, ^BSESN, ^NSEBANK | India VIX: ^INDIAVIX
- Macro: INR=X, BZ=F, GC=F, ^TNX, DX-Y.NYB
- Global: ^GSPC, ^IXIC, ^N225, ^HSI
- Optional CSV inputs: FII/DII flows, GIFT Nifty, PCR/OI (load if the file exists, skip gracefully if not)

## NON-NEGOTIABLE RULES

### 1. No look-ahead bias
- Every feature at time t uses only data known before the prediction time in IST.
- US markets close ~1:30–2:30 AM IST → the US session's return is only available to the NEXT Indian session.
- Asian cues are used only in the morning run.
- `tests/test_leakage.py` must check this: shift future data and confirm features don't change. Never weaken or skip this test.

### 2. Time-series validation only
- Walk-forward / TimeSeriesSplit. Never shuffle. Never use `train_test_split` with shuffle=True.
- Scalers and encoders are fit on training folds only.

### 3. Always compare against baselines
- Direction: always-up, previous-day direction, 20/50 EMA crossover.
- Range: VIX-implied 1-day range = Close × (VIX/100) / sqrt(252). The ML range model must beat this on coverage and width or it isn't used.

### 4. Honest reporting
- Report accuracy, precision, recall, ROC-AUC, calibration, range coverage, and pinball loss.
- Split metrics by VIX regime and event days (expiry, RBI, Budget).
- Treat direction accuracy above ~60% as a probable bug or leak. Investigate before reporting it.

### 5. Realistic backtest costs
Include brokerage, STT, exchange charges, GST, stamp duty, and slippage (all from config). Risk-free rate ~6.5% for Sharpe ratio.

## Domain notes
- Market hours: 9:15 AM–3:30 PM IST. Use the NSE holiday calendar, not the weekday alone.
- Expiry days are configurable (currently Nifty = Tuesday, Sensex = Thursday). SEBI changes these, so never hardcode them.
- Event flags: expiry, RBI policy, Union Budget, election results, results season, Muhurat trading.
- Separate models for Nifty and Sensex.

## Coding conventions
- Type hints and docstrings on public functions.
- All timestamps timezone-aware (Asia/Kolkata).
- Cache downloaded data to avoid re-fetching. Handle yfinance failures and missing days gracefully.
- Log the data timestamp used for every prediction.
- Dashboard always shows "Prediction for: [date], [today/tomorrow]", the last-updated time, and the disclaimer:
  "For educational purposes only. Not investment advice. Not SEBI-registered."

## Workflow
Build in stages: data → features → direction model → range model → backtest → UI.
After each stage, run the tests, show results, and wait for approval before moving on.
