"""Telegram delivery adapter; refuses to send without an explicit chat allowlist."""
import os, asyncio
from telegram import Bot
from security import parse_allowed_chat_ids
from daily_signal_service import run_daily_scan, format_report

async def send_report(text: str):
    token=os.getenv("TELEGRAM_BOT_TOKEN")
    allowed=parse_allowed_chat_ids()
    if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN belum diatur.")
    if not allowed: raise RuntimeError("TELEGRAM_ALLOWED_CHAT_IDS kosong; pengiriman ditolak.")
    async with Bot(token=token) as bot:
        for chat_id in sorted(allowed):
            await bot.send_message(chat_id=chat_id,text=text[:4096])

async def main():
    scan=run_daily_scan()
    await send_report(format_report(scan))
if __name__=="__main__": asyncio.run(main())
