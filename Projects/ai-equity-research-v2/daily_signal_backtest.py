
"""Single-position daily mark-to-market backtest. Research only."""
from __future__ import annotations

import math
import pandas as pd

from daily_signal_engine import calculate_indicators, DEFAULT_CONFIG


def backtest(
    bars: pd.DataFrame,
    config: dict | None = None,
    fee_bps: float = 10,
    slippage_bps: float = 10,
    risk_fraction: float = 0.01,
    max_allocation: float = 1.0,
    max_holding_sessions: int = 5,
) -> dict:
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Fee dan slippage tidak boleh negatif.")
    if not 0 < risk_fraction <= 0.05:
        raise ValueError("risk_fraction harus >0 dan <=5%.")
    if not 0 < max_allocation <= 1:
        raise ValueError("max_allocation harus >0 dan <=100%.")
    if not 1 <= max_holding_sessions <= 5:
        raise ValueError("Holding harus antara 1 dan 5 sesi.")

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(bars.columns):
        raise ValueError(f"Kolom wajib tidak lengkap: {sorted(required - set(bars.columns))}")

    cfg = {**DEFAULT_CONFIG, **(config or {})}
    x = calculate_indicators(bars)
    x = x.dropna(subset=[
        "SMA50", "EMA9", "EMA21", "RSI14",
        "MACD", "MACD_SIGNAL", "ATR14", "REL_VOLUME"
    ]).copy()

    if len(x) < 3:
        raise ValueError("Data historis tidak cukup untuk backtest.")

    cost = (fee_bps + slippage_bps) / 10000
    equity = 1.0
    trades = []
    curve_updates = {}
    i = 1

    while i < len(x) - 1:
        r, p = x.iloc[i], x.iloc[i - 1]

        conditions = [
            r.Close > r.EMA21,
            r.EMA9 > r.EMA21,
            r.MACD > r.MACD_SIGNAL,
            r.MACD > p.MACD,
            cfg["rsi_min"] <= r.RSI14 <= cfg["rsi_max"],
            r.REL_VOLUME >= cfg["min_relative_volume"],
            r.Close > r.SMA50,
        ]
        weights = [20, 20, 15, 10, 15, 10, 10]
        score = sum(w for ok, w in zip(conditions, weights) if ok)

        if score < cfg["min_score"]:
            i += 1
            continue

        entry_index = i + 1
        entry_bar = x.iloc[entry_index]
        raw_entry = float(entry_bar.Open)

        if not math.isfinite(raw_entry) or raw_entry <= 0:
            i += 1
            continue

        entry = raw_entry * (1 + cost)
        stop = max(
            0.01,
            float(r.Close) - cfg["atr_stop_multiple"] * float(r.ATR14)
        )
        risk_per_share = entry - stop

        if risk_per_share <= 0:
            i += 1
            continue

        risk_pct = risk_per_share / entry
        position_fraction = min(
            risk_fraction / risk_pct,
            max_allocation
        )
        target = entry + cfg["reward_risk_min"] * risk_per_share

        exit_price = None
        exit_reason = "time_exit"
        exit_index = entry_index
        last_index = min(entry_index + max_holding_sessions, len(x))

        for j in range(entry_index, last_index):
            day = x.iloc[j]
            day_open = float(day.Open)
            day_low = float(day.Low)
            day_high = float(day.High)

            # Conservative: stop has priority if both levels are touched.
            if day_low <= stop:
                exit_price = min(day_open, stop)
                exit_reason = "stop"
                exit_index = j
                break

            if day_high >= target:
                exit_price = target
                exit_reason = "target"
                exit_index = j
                break

            if j == last_index - 1:
                exit_price = float(day.Close)
                exit_reason = "time_exit"
                exit_index = j

        if exit_price is None:
            i += 1
            continue

        exit_net = exit_price * (1 - cost)
        net_return = exit_net / entry - 1
        equity_before = equity

        # Daily mark-to-market, including unrealized P/L while position is open.
        for j in range(entry_index, exit_index):
            mark = float(x.iloc[j].Close) * (1 - cost)
            mark_return = mark / entry - 1
            curve_updates[x.index[j]] = (
                equity_before * (1 + position_fraction * mark_return)
            )

        equity_after = equity_before * (
            1 + position_fraction * net_return
        )
        curve_updates[x.index[exit_index]] = equity_after
        equity = equity_after

        trades.append({
            "signal_date": str(x.index[i].date()),
            "entry_date": str(x.index[entry_index].date()),
            "exit_date": str(x.index[exit_index].date()),
            "entry": entry,
            "exit": exit_net,
            "reason": exit_reason,
            "return_pct": net_return * 100,
            "score": int(score),
            "position_pct": position_fraction * 100,
            "equity_before": equity_before,
            "equity_after": equity_after,
        })

        i = exit_index + 1

    # Carry the latest equity across flat days.
    curve = []
    current = 1.0
    for date in x.index:
        if date in curve_updates:
            current = curve_updates[date]
        curve.append({"date": str(date.date()), "equity": current})

    equity_series = pd.Series(
        [v["equity"] for v in curve],
        index=pd.to_datetime([v["date"] for v in curve]),
        dtype=float,
    )
    daily_returns = equity_series.pct_change().dropna()
    running_peak = equity_series.cummax()
    drawdowns = equity_series / running_peak - 1
    max_dd = float(drawdowns.min()) if len(drawdowns) else 0.0

    n = len(trades)
    returns = [t["return_pct"] for t in trades]
    wins = sum(v > 0 for v in returns)
    gross_wins = sum(v for v in returns if v > 0)
    gross_losses = abs(sum(v for v in returns if v < 0))

    days = max((x.index[-1] - x.index[0]).days, 1)
    total_return = equity - 1
    cagr = (equity ** (365.25 / days) - 1) * 100 if equity > 0 else -100

    daily_std = float(daily_returns.std(ddof=1)) if len(daily_returns) > 1 else 0.0
    sharpe = (
        float(daily_returns.mean() / daily_std * math.sqrt(252))
        if daily_std > 0 else 0.0
    )

    first_close = float(x.Close.iloc[0])
    last_close = float(x.Close.iloc[-1])
    benchmark_return = (
        last_close * (1 - cost) / (first_close * (1 + cost)) - 1
    ) * 100

    return {
        "trades": n,
        "win_rate_pct": wins / n * 100 if n else 0.0,
        "avg_return_pct": sum(returns) / n if n else 0.0,
        "profit_factor": (
            gross_wins / gross_losses if gross_losses > 0
            else (float("inf") if gross_wins > 0 else 0.0)
        ),
        "max_drawdown_pct": max_dd * 100,
        "ending_equity_index": equity,
        "total_return_pct": total_return * 100,
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "benchmark_buy_hold_pct": benchmark_return,
        "risk_per_trade_pct": risk_fraction * 100,
        "max_allocation_pct": max_allocation * 100,
        "max_holding_sessions": max_holding_sessions,
        "cost_bps_round_trip": 2 * (fee_bps + slippage_bps),
        "trades_detail": trades,
        "equity_curve": curve,
        "limitations": (
            "Mark-to-market menggunakan harga penutupan harian; belum "
            "memodelkan spread aktual, pajak, corporate actions, suspensi, "
            "market impact, dan survivorship bias."
        ),
    }