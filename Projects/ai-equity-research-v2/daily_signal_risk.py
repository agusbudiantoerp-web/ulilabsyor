"""Trade planning and position sizing. Outputs are indicative, not broker instructions."""
from __future__ import annotations
def build_trade_plan(close: float, atr: float, equity: float, risk_pct: float=1.0,
                    atr_multiple: float=1.5, reward_risk: float=2.0,
                    entry_buffer_pct: float=1.0, max_position_pct: float=20.0) -> dict:
    vals=[close,atr,equity,risk_pct,atr_multiple,reward_risk,entry_buffer_pct,max_position_pct]
    if any(float(v)<=0 for v in vals): raise ValueError("Semua input harus positif.")
    if risk_pct>5 or max_position_pct>100: raise ValueError("Batas risiko/posisi tidak wajar.")
    stop=max(0.01,close-atr*atr_multiple); per_share=close-stop
    risk_budget=equity*risk_pct/100
    shares_by_risk=int(risk_budget/per_share) if per_share>0 else 0
    shares_by_cap=int(equity*(max_position_pct/100)/close)
    shares=max(0,min(shares_by_risk,shares_by_cap))
    entry_low=close*(1-entry_buffer_pct/100); entry_high=close*(1+entry_buffer_pct/100)
    target=close+reward_risk*per_share
    return {"entry_low":entry_low,"entry_high":entry_high,"stop_loss":stop,"target":target,
      "risk_per_share":per_share,"risk_budget":risk_budget,"shares":shares,
      "position_value":shares*close,"portfolio_weight_pct":shares*close/equity*100,
      "planned_loss":shares*per_share,"reward_risk":(target-close)/per_share}
def validate_entry(current_price: float, entry_low: float, entry_high: float) -> dict:
    if min(current_price,entry_low,entry_high)<=0 or entry_low>entry_high:
        raise ValueError("Rentang harga tidak valid.")
    valid=entry_low<=current_price<=entry_high
    return {"valid":valid,"status":"ENTRY_WITHIN_ZONE" if valid else "GAP_OR_OUTSIDE_ZONE",
      "message":"Harga masih dalam zona indikatif." if valid else "Jangan mengejar harga; kandidat dibatalkan di luar zona entry."}
