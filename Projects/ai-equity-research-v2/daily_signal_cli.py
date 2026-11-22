"""CLI for daily scan, history and readable historical backtest reports."""
from __future__ import annotations

import argparse
import json
import math

from daily_signal_service import run_daily_scan, format_report, get_dashboard_data
from daily_signal_engine import load_daily_history
from daily_signal_backtest import backtest


def _fmt(value, digits=2, suffix=""):
    try:
        number = float(value)
        if math.isinf(number):
            return "∞" if number > 0 else "-∞"
        return f"{number:,.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def format_backtest_report(ticker: str, market: str, result: dict) -> str:
    """Create a human-readable backtest report with explicit limitations."""
    trades = int(result.get("trades", 0) or 0)
    lines = [
        "📈 AI EQUITY RESEARCH — HISTORICAL BACKTEST",
        f"Instrumen: {ticker} | Pasar: {market} | Horizon data: 5 tahun",
        f"Jumlah transaksi: {trades}",
        f"Win rate: {_fmt(result.get('win_rate_pct'), suffix='%')}",
        f"Rata-rata return per transaksi: {_fmt(result.get('avg_return_pct'), suffix='%')}",
        f"Profit factor: {_fmt(result.get('profit_factor'))}",
        f"Maximum drawdown: {_fmt(result.get('max_drawdown_pct'), suffix='%')}",
        f"Total return strategi: {_fmt(result.get('total_return_pct'), suffix='%')}",
        f"CAGR strategi: {_fmt(result.get('cagr_pct'), suffix='%')}",
        f"Sharpe ratio: {_fmt(result.get('sharpe_ratio'))}",
        f"Buy-and-hold benchmark: {_fmt(result.get('benchmark_buy_hold_pct'), suffix='%')}",
        f"Risk budget per transaksi: {_fmt(result.get('risk_per_trade_pct'), suffix='%')}",
        f"Maksimum alokasi posisi: {_fmt(result.get('max_allocation_pct'), suffix='%')}",
        f"Holding maksimum: {result.get('max_holding_sessions', 'N/A')} sesi",
        f"Estimasi biaya round-trip: {_fmt(result.get('cost_bps_round_trip'), digits=0)} bps",
    ]
    if not trades:
        lines.append("Catatan: tidak ada transaksi yang memenuhi aturan strategi pada periode uji.")
    lines.extend([
        "",
        "INTERPRETASI",
        "• Hasil historis bukan jaminan hasil masa depan dan bukan rekomendasi transaksi.",
        "• Bandingkan strategi dengan benchmark, drawdown, jumlah transaksi, serta biaya.",
        "• Lakukan walk-forward dan paper trading sebelum mempertimbangkan penggunaan nyata.",
        "",
        "BATASAN MODEL",
        str(result.get("limitations", "Tidak ada keterangan batasan.")),
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AI Daily Stock Signal — IDX/US")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan")
    scan.add_argument("--market", choices=["IDX", "US"], action="append")
    scan.add_argument("--symbols", nargs="*")

    history = sub.add_parser("history")
    history.add_argument("--limit", type=int, default=50)

    bt = sub.add_parser("backtest")
    bt.add_argument("symbol")
    bt.add_argument("market", choices=["IDX", "US"])
    bt.add_argument("--json", action="store_true", help="Cetak hasil lengkap termasuk detail transaksi dalam JSON")
    bt.add_argument("--fee-bps", type=float, default=10.0)
    bt.add_argument("--slippage-bps", type=float, default=10.0)
    bt.add_argument("--risk-fraction", type=float, default=0.01)
    bt.add_argument("--max-allocation", type=float, default=1.0)
    bt.add_argument("--max-holding-sessions", type=int, default=5)

    args = parser.parse_args()
    if args.command == "scan":
        universe = None
        if args.symbols:
            markets = args.market or ["IDX"]
            if len(markets) != 1:
                parser.error("--symbols harus dipasangkan dengan tepat satu --market")
            universe = {markets[0]: args.symbols}
        result = run_daily_scan(universe=universe)
        print(format_report(result))
        print("\nRINGKASAN JSON\n" + json.dumps(result["counts"], indent=2))
    elif args.command == "history":
        print(json.dumps(get_dashboard_data(args.limit), indent=2, default=str))
    elif args.command == "backtest":
        bars, meta = load_daily_history(args.symbol, args.market, "5y")
        result = backtest(
            bars,
            fee_bps=args.fee_bps,
            slippage_bps=args.slippage_bps,
            risk_fraction=args.risk_fraction,
            max_allocation=args.max_allocation,
            max_holding_sessions=args.max_holding_sessions,
        )
        if args.json:
            print(json.dumps({"ticker": meta["ticker"], "market": meta["market"], "result": result}, indent=2, default=str))
        else:
            print(format_backtest_report(meta["ticker"], meta["market"], result))


if __name__ == "__main__":
    main()
