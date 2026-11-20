"""SQLite storage for scans, daily signals and forward returns."""
from __future__ import annotations
import sqlite3, json, os
from pathlib import Path
from datetime import datetime, timezone

def connect(db_path: str | None = None):
    path = db_path or os.getenv("DAILY_SIGNAL_DB","data/daily_signals.sqlite3")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30); db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db
def initialize(db_path: str | None = None):
    with connect(db_path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, scanned INTEGER, failed INTEGER, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS signals(id INTEGER PRIMARY KEY, scan_id INTEGER NOT NULL, market TEXT, ticker TEXT, bar_date TEXT, signal TEXT, score INTEGER, close REAL, entry_low REAL, entry_high REAL, stop_loss REAL, target REAL, reward_risk REAL, payload TEXT NOT NULL, UNIQUE(market,ticker,bar_date));
        CREATE TABLE IF NOT EXISTS outcomes(id INTEGER PRIMARY KEY, signal_id INTEGER NOT NULL, horizon INTEGER NOT NULL, observed_date TEXT, close REAL, return_pct REAL, UNIQUE(signal_id,horizon));
        CREATE INDEX IF NOT EXISTS idx_signals_date ON signals(bar_date DESC);
        """)
def save_scan(scan: dict, db_path: str | None = None) -> int:
    initialize(db_path)
    with connect(db_path) as db:
        cur = db.execute("INSERT INTO scans(created_at,scanned,failed,payload) VALUES(?,?,?,?)",
          (datetime.now(timezone.utc).isoformat(),scan.get("counts",{}).get("scanned",0),scan.get("counts",{}).get("failed",0),json.dumps(scan,default=str)))
        scan_id = cur.lastrowid
        for s in scan.get("results",[]):
            db.execute("""INSERT OR IGNORE INTO signals(scan_id,market,ticker,bar_date,signal,score,close,entry_low,entry_high,stop_loss,target,reward_risk,payload)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (scan_id,s.get("market"),s.get("ticker"),s.get("bar_date"),s.get("signal"),s.get("score"),s.get("close"),s.get("entry_low"),s.get("entry_high"),s.get("stop_loss"),s.get("target"),s.get("reward_risk"),json.dumps(s,default=str)))
        return int(scan_id)
def latest_scan(db_path: str | None = None):
    initialize(db_path)
    with connect(db_path) as db:
        row = db.execute("SELECT payload FROM scans ORDER BY id DESC LIMIT 1").fetchone()
        return json.loads(row["payload"]) if row else None
def signal_history(limit: int = 100, db_path: str | None = None):
    initialize(db_path)
    with connect(db_path) as db:
        rows = db.execute("SELECT * FROM signals ORDER BY bar_date DESC,id DESC LIMIT ?",(max(1,min(int(limit),1000)),)).fetchall()
        return [dict(r) for r in rows]
def record_outcome(signal_id: int, horizon: int, observed_date: str, close: float, db_path: str | None = None):
    if horizon not in (1,3,5): raise ValueError("Horizon hanya 1, 3, atau 5 sesi.")
    initialize(db_path)
    with connect(db_path) as db:
        row = db.execute("SELECT close FROM signals WHERE id=?",(signal_id,)).fetchone()
        if not row or not row["close"]: raise ValueError("Signal tidak ditemukan atau harga awal tidak valid.")
        ret = (float(close)/float(row["close"])-1)*100
        db.execute("INSERT OR REPLACE INTO outcomes(signal_id,horizon,observed_date,close,return_pct) VALUES(?,?,?,?,?)",
          (signal_id,horizon,observed_date,float(close),ret))
