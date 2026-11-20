"""CLI: python daily_signal_cli.py scan|history|backtest SYMBOL MARKET."""
import argparse, json
from daily_signal_service import run_daily_scan, format_report, get_dashboard_data
from daily_signal_engine import load_daily_history
from daily_signal_backtest import backtest

def main():
    p=argparse.ArgumentParser(description="AI Daily Stock Signal — IDX/US")
    sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("scan"); s.add_argument("--market",choices=["IDX","US"],action="append"); s.add_argument("--symbols",nargs="*")
    h=sub.add_parser("history"); h.add_argument("--limit",type=int,default=50)
    b=sub.add_parser("backtest"); b.add_argument("symbol"); b.add_argument("market",choices=["IDX","US"])
    args=p.parse_args()
    if args.command=="scan":
        universe=None
        if args.symbols:
            markets=args.market or ["IDX"]
            if len(markets)!=1: p.error("--symbols harus dipasangkan dengan tepat satu --market")
            universe={markets[0]:args.symbols}
        result=run_daily_scan(universe=universe)
        print(format_report(result)); print("\nRINGKASAN JSON\n"+json.dumps(result["counts"],indent=2))
    elif args.command=="history":
        print(json.dumps(get_dashboard_data(args.limit),indent=2,default=str))
    elif args.command=="backtest":
        bars,meta=load_daily_history(args.symbol,args.market,"5y")
        print(json.dumps({"ticker":meta["ticker"],"market":meta["market"],"result":backtest(bars)},indent=2,default=str))
if __name__=="__main__": main()
