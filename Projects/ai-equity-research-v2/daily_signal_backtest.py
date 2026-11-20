"""Basic long-only backtest; signals at close, entries at next open."""
from __future__ import annotations
import pandas as pd
from daily_signal_engine import calculate_indicators, DEFAULT_CONFIG

def backtest(bars: pd.DataFrame, config: dict | None = None, fee_bps: float = 10,
             slippage_bps: float = 10, risk_fraction: float = 0.01) -> dict:
    if fee_bps < 0 or slippage_bps < 0 or not 0 < risk_fraction <= 0.05:
        raise ValueError("Biaya non-negatif; risk_fraction harus >0 dan <=5%.")
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    x = calculate_indicators(bars).dropna(subset=["SMA50","EMA9","EMA21","RSI14","MACD","MACD_SIGNAL","ATR14","REL_VOLUME"])
    trades=[]; equity=1.0; peak=1.0; max_dd=0.0; cost=(fee_bps+slippage_bps)/10000
    for i in range(1,len(x)-1):
        r,p=x.iloc[i],x.iloc[i-1]
        conditions=[r.Close>r.EMA21,r.EMA9>r.EMA21,r.MACD>r.MACD_SIGNAL,r.MACD>p.MACD,
                    cfg["rsi_min"]<=r.RSI14<=cfg["rsi_max"],r.REL_VOLUME>=cfg["min_relative_volume"],r.Close>r.SMA50]
        score=sum(w for ok,w in zip(conditions,[20,20,15,10,15,10,10]) if ok)
        if score < cfg["min_score"]: continue
        nxt=x.iloc[i+1]; entry=float(nxt.Open)*(1+cost)
        stop=max(0.01,float(r.Close)-cfg["atr_stop_multiple"]*float(r.ATR14))
        risk=entry-stop
        if risk<=0: continue
        target=entry+cfg["reward_risk_min"]*risk
        exit_price=None; reason="time_exit"
        for j in range(i+1,min(i+6,len(x))):
            day=x.iloc[j]
            # Conservative ordering: if both touched on one bar, assume stop first.
            if day.Low<=stop: exit_price=stop*(1-cost); reason="stop"; break
            if day.High>=target: exit_price=target*(1-cost); reason="target"; break
        if exit_price is None: exit_price=float(x.iloc[min(i+5,len(x)-1)].Close)*(1-cost)
        ret=exit_price/entry-1
        equity *= 1 + ret*risk_fraction/(risk/entry)
        peak=max(peak,equity); max_dd=min(max_dd,equity/peak-1)
        trades.append({"signal_date":str(x.index[i]),"entry_date":str(x.index[i+1]),"entry":entry,
                       "exit":exit_price,"reason":reason,"return_pct":ret*100,"score":int(score)})
    n=len(trades); wins=sum(t["return_pct"]>0 for t in trades)
    return {"trades":n,"win_rate_pct":wins/n*100 if n else 0,
      "avg_return_pct":sum(t["return_pct"] for t in trades)/n if n else 0,
      "max_drawdown_pct":max_dd*100,"ending_equity_index":equity,
      "cost_bps_round_trip":2*(fee_bps+slippage_bps),"trades_detail":trades,
      "limitations":"Belum memodelkan spread aktual, pajak, corporate actions, suspensi, dan market impact."}
