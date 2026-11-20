# AI Daily Stock Signal — Development Plan

## Product decision

Extend AI Equity Research V2 into a daily short-term (1–5 trading sessions) signal research system for IDX and US equities. Deliver results to the RagLeap dashboard and an allowlisted Telegram chat. The system is research/decision support only: no broker integration, order placement, or guaranteed-return language.

## Existing V2 assets to reuse

- `engine.py`: `analyze_equity(symbol, period, market)`, price history, SMA 20/50/200, RSI 14, volatility, financial data and data-quality warnings.
- `market_engine.py`: explicit IDX/US ticker normalization.
- `bot.py` and `security.py`: Telegram polling bot and fail-closed chat-ID allowlist.
- `app.py`: Streamlit dashboard.
- `scenario_engine.py`, DCF and Multi-Stage DCF: retain as optional fundamental context, not as the primary 1–5 day trigger.

## Proposed architecture

1. **Market data adapter** — normalize OHLCV bars, exchange, currency, source, retrieval time and latest completed-session date. Start with the existing Yahoo Finance integration behind an adapter; keep provider replaceable. Reject empty, stale, malformed or incomplete bars.
2. **Technical signal engine** — deterministic, testable calculations for EMA 9/21, RSI 14, MACD 12/26/9, ATR 14, relative volume and recent high/low levels. Never let an LLM calculate indicators or invent prices.
3. **Candidate scoring** — configurable rules and weighted score. Initial research hypothesis only (not validated): price above EMA 21; EMA 9 above EMA 21; positive/improving MACD; RSI in a configurable momentum band; relative volume above threshold. Return WATCH / BUY_CANDIDATE / NO_TRADE, not an unconditional buy instruction.
4. **Risk engine** — derive entry zone from completed-session close and/or breakout level; calculate ATR-based invalidation/stop, target and risk/reward. If price gaps beyond the entry zone or risk/reward is inadequate, invalidate the candidate. Position sizing is informational and requires user-defined portfolio risk.
5. **Persistence and audit** — PostgreSQL tables for scan runs, candidates/signals, market-data provenance, rule-set version and subsequent 1/3/5-session outcomes. Unique key prevents duplicate daily messages.
6. **Scheduler** — run at 07:30 Asia/Jakarta on weekdays, with exchange-calendar/session checks and data freshness checks per market. Send a clear NO_TRADE report when no candidate passes. Retry transient provider failures safely; never silently reuse stale data.
7. **Delivery** — extend the existing allowlisted Telegram bot with a scheduled report and commands for status/last report. Add a RagLeap dashboard view for latest scan, signal rationale, risk levels, data timestamp/source, warnings and history.
8. **Evaluation gate** — unit tests, historical backtest with transaction costs/slippage, out-of-sample/walk-forward validation and paper-trading observation before treating any rule set as useful. Store every signal including rejected/no-trade outcomes to reduce selection bias.

## Initial daily report

- Run time: 07:30 WIB.
- Universe: configurable liquid IDX and US ticker lists; do not claim full-market coverage until universe and provider coverage are verified.
- For each candidate: market, ticker/company, last completed bar date, price/currency, signal state, entry zone, stop/invalidation, target, estimated reward/risk, score, key rule checks, data source and freshness warnings.
- Explicitly state that the report uses the last completed trading session and is not a live intraday quote.
- If no data is fresh or the exchange is closed, say so; do not manufacture a signal.

## Delivery phases

### Phase 1 — Signal engine (first implementation)
- Add pure functions for indicator calculation, rule evaluation, entry/stop/target and freshness validation.
- Add fixtures and tests for valid, stale, missing-volume, gap-up and no-signal cases.
- Do not change the existing V2 DCF engine or production Streamlit app behavior.

### Phase 2 — Database and scanner
- Add PostgreSQL persistence and configurable IDX/US universes.
- Run a manual scan and inspect stored candidates before enabling a schedule.

### Phase 3 — RagLeap dashboard and Telegram
- Add dashboard page and scheduled Telegram delivery, preserving allowlist security.
- Add dry-run mode and explicit duplicate-send protection.

### Phase 4 — Backtest and paper trading
- Evaluate historical and forward paper results; revise rules only from measured evidence.

## Safety and data-quality requirements

- No automatic broker orders.
- Never represent a candidate as a guaranteed winner or personalized financial advice.
- Distinguish daily close from real-time/pre-market data and show exact timestamp/timezone.
- Missing data is unknown, not zero. Currency and ticker mapping must be explicit.
- Account for corporate actions, split/dividend adjustments, trading halts, liquidity, spreads, transaction costs, slippage and market holidays.
- Avoid look-ahead bias: a signal formed from session T close is only actionable after that close; backtests must model next-session execution.
- Keep Telegram credentials and chat IDs in environment variables, never in Git.
