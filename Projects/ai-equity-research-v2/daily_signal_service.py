"""Shared service used by CLI, dashboard and messaging adapters."""
from daily_signal_scanner import scan_universe
from daily_signal_storage import save_scan, latest_scan, signal_history

def run_daily_scan(universe=None, config=None, db_path=None, max_workers=4):
    result = scan_universe(universe=universe, config=config, max_workers=max_workers)
    result["scan_id"] = save_scan(result, db_path=db_path)
    return result

def get_dashboard_data(limit=100, db_path=None):
    return {"latest":latest_scan(db_path=db_path),"history":signal_history(limit=limit,db_path=db_path)}

def format_report(scan: dict) -> str:
    c=scan.get("counts",{})
    lines=["AI DAILY STOCK SIGNAL — IDX + US",
      f"Dipindai: {c.get('scanned',0)} | Berhasil: {c.get('success',0)} | Gagal: {c.get('failed',0)}",
      f"BUY CANDIDATE: {c.get('buy_candidate',0)} | WATCH: {c.get('watch',0)} | NO TRADE: {c.get('no_trade',0)}",""]
    candidates=[s for s in scan.get("results",[]) if s.get("signal")=="BUY_CANDIDATE"]
    if not candidates: lines.append("Tidak ada kandidat yang memenuhi seluruh kriteria saat pemindaian.")
    for s in candidates:
      lines.append(f"{s.get('market')} {s.get('ticker')} | skor {s.get('score')}/100 | close {s.get('close'):,.2f} {s.get('currency')}")
      lines.append(f"Entry indikatif {s.get('entry_low'):,.2f}–{s.get('entry_high'):,.2f} | Stop {s.get('stop_loss'):,.2f} | Target {s.get('target'):,.2f} | R/R {s.get('reward_risk'):.2f}")
      lines.append(f"Bar: {s.get('bar_date')} | RSI {s.get('rsi14'):.1f} | RelVol {s.get('relative_volume'):.2f}x")
    lines += ["","Data: Yahoo Finance; berdasarkan bar harian terakhir yang tersedia.",
      "Kandidat riset, bukan perintah beli/jual atau nasihat investasi. Verifikasi likuiditas, spread, dan harga saat eksekusi."]
    return "\n".join(lines)
