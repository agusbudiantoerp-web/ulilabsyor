# AI Equity Research V1

Shared Python research engine for Streamlit and Telegram, initially focused on IDX tickers (.JK).

## Features
- Market history, SMA 20/50/200, RSI 14 and historical annualized volatility.
- Available financial statement fields and simplified illustrative DCF.
- Excel and PDF reports.
- Telegram /analyze command protected by a fail-closed chat-ID allowlist.

## Windows PowerShell setup
~~~powershell
cd Projects/ai-equity-research
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
~~~

## Telegram local test
1. Create a bot using Telegram BotFather; keep its token private.
2. Obtain your numeric Telegram chat ID privately.
3. Set both variables in PowerShell; never commit them to GitHub:
~~~powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
$env:TELEGRAM_ALLOWED_CHAT_IDS="123456789"
python bot.py
~~~
Replace the example ID with your own numeric chat ID. Multiple IDs may be comma-separated. Bot refuses to start without an allowlist and denies all other chats.

## Live data smoke test (manual)
After installing dependencies, run:
~~~powershell
python validate_live.py
~~~
This checks whether Yahoo Finance returns data for ANTM, BBCA and PTBA, and prints the latest price/report periods, statement values, DCF availability and automatic data warnings. It does not prove the financial statement mapping is correct. Compare each period and unit with the issuer's audited report before using the values.

## Free deployment
- Web: Streamlit Community Cloud; app root is this folder and entrypoint is app.py.
- Telegram: local polling is for development; continuous free worker availability is not guaranteed.
- GitHub Pages cannot host a continuously running Python bot. The calculation engine does not require a paid AI API.

## Limitations
Yahoo Finance is third-party data, not official IDX data. Coverage, timing and statement fields vary. Verify currency, units and accounting periods. Missing data is not zero. DCF is aggregate illustrative enterprise value, not per-share fair value; it does not yet normalize taxes, working capital, diluted shares, net debt, minority interests or segment forecasts. Technical indicators are not standalone trading signals. Not investment advice.

## Next gates
Validate live issuer data and statement units; then add per-share valuation, scenario analysis and source-quality flags. Deploy only after tests and manual review.

## Final Daily Report + Gemma

Daily report menyertakan kandidat prioritas, watchlist, data gagal, dan bagian khusus TPIA (termasuk ketika statusnya `NO_TRADE`). Ollama lokal memakai `gemma4:latest`; komentar AI diminta dalam Bahasa Indonesia dengan struktur ringkasan pasar, prioritas, risiko, TPIA, dan rencana sesi berikutnya.

Pengaturan Ollama opsional di `.env`:

```env
OLLAMA_URL=http://127.0.0.1:11434/api/generate
OLLAMA_MODEL=gemma4:latest
OLLAMA_TIMEOUT_SECONDS=300
OLLAMA_NUM_PREDICT=650
```

## Final backtest report

```powershell
python daily_signal_cli.py backtest BBCA IDX
```

Perintah menampilkan metrik backtest dalam format ringkas. Untuk seluruh detail transaksi dalam JSON:

```powershell
python daily_signal_cli.py backtest BBCA IDX --json
```

Parameter biaya dan pengelolaan risiko dapat diatur melalui opsi `--fee-bps`, `--slippage-bps`, `--risk-fraction`, `--max-allocation`, dan `--max-holding-sessions`.

## Final validation

Jalankan `FINAL_TESTS.bat` dari folder proyek setelah dependensi pada `requirements.txt` tersedia. Pengujian ini tidak mengirim Telegram dan tidak mengubah Task Scheduler.
