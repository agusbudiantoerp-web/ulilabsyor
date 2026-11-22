"""Parallel scanner for configured IDX and US watchlists."""
from __future__ import annotations
import json, os
from concurrent.futures import ThreadPoolExecutor
from daily_signal_engine import scan_symbol

DEFAULT_UNIVERSE = {
 "IDX": ["BBCA","BBRI","BMRI","BBNI","ANTM","ADRO","PTBA","TLKM","ASII","ICBP","INDF","KLBF","MDKA","TPIA","GOTO"],
 "US": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","JPM","XOM","SPY","QQQ"]
}
def load_universe(path: str | None = None) -> dict:
    path = path or os.getenv("DAILY_SIGNAL_UNIVERSE_FILE")
    if not path: return DEFAULT_UNIVERSE
    with open(path, encoding="utf-8") as f: raw = json.load(f)
    return {m: [str(s).strip().upper() for s in syms] for m, syms in raw.items() if m in ("IDX","US")}
def scan_universe(universe: dict | None = None, config: dict | None = None, max_workers: int = 1) -> dict:
    universe = universe or load_universe()
    jobs = []
    with ThreadPoolExecutor(max_workers=max(1,min(int(max_workers),8))) as pool:
        for market, symbols in universe.items():
            if market not in ("IDX","US"): continue
            for symbol in symbols:
                jobs.append((market, symbol, pool.submit(scan_symbol, symbol, market, config=config)))
        results, errors = [], []
        for market, symbol, future in jobs:
            try: results.append(future.result())
            except Exception as exc: errors.append({"market":market,"symbol":symbol,"error":str(exc)})
    results.sort(key=lambda r: (r["signal"]=="BUY_CANDIDATE", r["score"]), reverse=True)
    return {"results":results,"errors":errors,"counts":{
      "scanned":len(jobs),"success":len(results),"failed":len(errors),
      "buy_candidate":sum(r["signal"]=="BUY_CANDIDATE" for r in results),
      "watch":sum(r["signal"]=="WATCH" for r in results),
      "no_trade":sum(r["signal"]=="NO_TRADE" for r in results)}}
