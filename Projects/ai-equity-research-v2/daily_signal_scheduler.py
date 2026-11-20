"""Simple scheduler runner. Use Windows Task Scheduler or cron for production."""
import argparse, time
from datetime import datetime
from zoneinfo import ZoneInfo
from daily_signal_service import run_daily_scan, format_report
from daily_signal_telegram import send_report
import asyncio

def run_once():
    result=run_daily_scan()
    report=format_report(result)
    print(report,flush=True)
    if result.get("counts",{}).get("success",0):
        asyncio.run(send_report(report))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--loop",action="store_true",help="Poll every 60 seconds; run at configured local time.")
    p.add_argument("--hour",type=int,default=7); p.add_argument("--minute",type=int,default=30)
    args=p.parse_args()
    if not args.loop: run_once(); return
    last=None
    while True:
        now=datetime.now(ZoneInfo("Asia/Jakarta"))
        key=now.strftime("%Y-%m-%d")
        if now.weekday()<5 and now.hour==args.hour and now.minute==args.minute and last!=key:
            run_once(); last=key
        time.sleep(30)
if __name__=="__main__": main()
