"""Telegram delivery adapter; refuses to send without an explicit chat allowlist."""
from __future__ import annotations
import os
from security import parse_allowed_chat_ids

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELEGRAM_MESSAGE_LIMIT = 3900  # safely below Telegram's 4096-character limit

def _chunks(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    text = str(text or "").strip()
    if not text:
        return ["Laporan AI Equity Research kosong."]
    chunks=[]
    while len(text) > limit:
        cut=text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut=limit
        chunks.append(text[:cut].strip())
        text=text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks

async def send_report(text: str):
    token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    allowed=parse_allowed_chat_ids()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diatur pada file .env.")
    if not allowed:
        raise RuntimeError("TELEGRAM_ALLOWED_CHAT_IDS kosong; pengiriman ditolak.")
    from telegram import Bot
    async with Bot(token=token) as bot:
        for chat_id in sorted(allowed):
            for part in _chunks(text):
                await bot.send_message(chat_id=chat_id, text=part, disable_web_page_preview=True)

async def main():
    from daily_signal_service import run_daily_scan, format_report
    scan=run_daily_scan()
    await send_report(format_report(scan))

if __name__=="__main__":
    import asyncio
    asyncio.run(main())
