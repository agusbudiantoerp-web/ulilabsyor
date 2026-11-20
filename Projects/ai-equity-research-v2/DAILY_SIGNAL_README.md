# AI Daily Stock Signal

Short-term (1–5 trading sessions) research scanner for IDX and US equities. It does not place broker orders.

## Modules
- `daily_signal_engine.py`: Yahoo daily bars, technical indicators, deterministic score and candidate status.
- `daily_signal_scanner.py`: configurable IDX and US watchlists.
- `daily_signal_risk.py`: ATR stop, target, risk budget, position sizing and entry-gap validation.
- `daily_signal_portfolio.py`: exposure cap, max positions and candidate allocation.
- `daily_signal_storage.py`: SQLite scan, signal and outcome history.
- `daily_signal_outcomes.py`: evaluates forward 1/3/5-session returns.
- `daily_signal_backtest.py`: next-session-open simulation with fee/slippage assumptions.
- `daily_signal_service.py`: shared service and report formatting.
- `daily_signal_cli.py`: scan, history and backtest commands.
- `daily_signal_telegram.py`: Telegram delivery protected by chat allowlist.
- `daily_signal_api.py`: optional FastAPI router to mount in RagLeap.
- `daily_signal_scheduler.py`: scheduled runner.

## Install and commands
```powershell
cd Projects\ai-equity-research-v2
python -m pip install -r requirements.txt
python daily_signal_cli.py scan
python daily_signal_cli.py history
python daily_signal_cli.py backtest BBCA IDX
pytest -q tests/test_daily_signal_engine.py
```

## Telegram
Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_CHAT_IDS` environment variables. Chat IDs are comma-separated numeric IDs. Never commit credentials. Run `python daily_signal_telegram.py` to scan and send.

## Scheduling
Use Windows Task Scheduler to run `python daily_signal_scheduler.py` on weekdays at 07:30 Asia/Jakarta. `python daily_signal_scheduler.py --loop` is also available. Add exchange holiday/session-calendar validation before relying on scheduled output.

## Custom universe
Set `DAILY_SIGNAL_UNIVERSE_FILE` to a JSON file such as:
```json
{"IDX":["BBCA","ANTM"],"US":["AAPL","NVDA"]}
```

## Limitations and controls
Default universe is a starter watchlist, not full-market coverage. Yahoo Finance bars are third-party and freshness uses calendar age, not an authoritative exchange calendar. Rules and score are unvalidated research hypotheses. Backtest is simplified and must be reviewed for survivorship bias, corporate actions, spread, taxes, liquidity, market impact and intrabar stop/target ambiguity. Use walk-forward validation and paper trading before considering live decisions. Entry/stop/target are indicative, not executable quotes or personalized advice.
