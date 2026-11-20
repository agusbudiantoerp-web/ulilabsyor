# AI Daily Stock Signal

Short-term (1–5 trading sessions) research scanner for IDX and US equities. It does not place broker orders.

## Included modules
- `daily_signal_engine.py`: Yahoo daily bars, indicators, deterministic scoring, entry/stop/target.
- `daily_signal_scanner.py`: configurable IDX and US watchlists.
- `daily_signal_storage.py`: SQLite scan, signal and 1/3/5-session outcome history.
- `daily_signal_backtest.py`: next-session-open historical simulation with fee/slippage assumptions.
- `daily_signal_service.py`: shared service and human-readable report.
- `daily_signal_cli.py`: scan, history and backtest commands.
- `daily_signal_telegram.py`: Telegram delivery with fail-closed allowlist.
- `daily_signal_api.py`: optional FastAPI router for RagLeap integration.
- `daily_signal_scheduler.py`: scheduled runner.

## Install and run (PowerShell)
```powershell
cd Projects\ai-equity-research-v2
python -m pip install -r requirements.txt
python daily_signal_cli.py scan
python daily_signal_cli.py history
python daily_signal_cli.py backtest BBCA IDX
```

## Telegram
Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_CHAT_IDS` as environment variables. The latter is a comma-separated list of numeric chat IDs. Never commit credentials.

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TELEGRAM_ALLOWED_CHAT_IDS="123456789"
python daily_signal_telegram.py
```

## Scheduling
Use Windows Task Scheduler to run `python daily_signal_scheduler.py` on weekdays at 07:30 Asia/Jakarta. For a continuous process, `python daily_signal_scheduler.py --loop` is available. Configure separate market calendars/holidays before treating the report time as an exchange-open guarantee.

## Universe
Default watchlist is a starter list, not the full IDX or US market. Override using JSON path in `DAILY_SIGNAL_UNIVERSE_FILE`, e.g.:
```json
{"IDX":["BBCA","ANTM"],"US":["AAPL","NVDA"]}
```

## Important limitations
Signals use the latest bar returned by Yahoo Finance; freshness validation blocks data older than five calendar days, but does not provide an exchange-calendar-aware completeness guarantee. The initial score/rules are hypotheses, not validated alpha. Backtest is simplified and must be reviewed for survivorship bias, corporate actions, intrabar stop/target ambiguity, taxes, spreads, liquidity and execution costs. Paper-trade and walk-forward validate before live use. Entry/stop/target are indicative calculations, not executable quotes or personalized advice.
