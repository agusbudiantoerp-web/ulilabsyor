"""Evaluate stored signals after 1, 3 and 5 completed sessions."""
from __future__ import annotations
import pandas as pd
from daily_signal_engine import load_daily_history
from daily_signal_storage import signal_history, record_outcome

def update_forward_outcomes(db_path=None, limit=500):
    rows=signal_history(limit=limit,db_path=db_path); updated=[]; errors=[]
    for row in rows:
        try:
            market=row["market"]; ticker=row["ticker"]
            bars,_=load_daily_history(ticker,market,"3mo")
            dates=[d for d in bars.index if d.date().isoformat()>row["bar_date"]]
            for horizon in (1,3,5):
                if len(dates)<horizon: continue
                dt=dates[horizon-1]; close=float(bars.loc[dt,"Close"])
                record_outcome(row["id"],horizon,dt.date().isoformat(),close,db_path=db_path)
                updated.append({"signal_id":row["id"],"horizon":horizon,"return_pct":(close/row["close"]-1)*100})
        except Exception as exc: errors.append({"signal_id":row["id"],"error":str(exc)})
    return {"updated":updated,"errors":errors}
