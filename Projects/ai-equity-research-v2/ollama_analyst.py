"""Local Ollama analysis for the AI Equity Research daily Telegram report."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "gemma4:latest"
DEFAULT_NUM_PREDICT = 650


def _generate(prompt: str, url: str, model: str, timeout: int, num_predict: int) -> dict:
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict,
            "num_ctx": 4096,
            "repeat_penalty": 1.05,
        },
        "keep_alive": "10m",
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def analyze_report(report: str) -> str:
    """Return a structured, cautious Indonesian analysis grounded in source report."""
    url = os.getenv("OLLAMA_URL", DEFAULT_URL).strip() or DEFAULT_URL
    model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))
    num_predict = max(400, int(os.getenv("OLLAMA_NUM_PREDICT", str(DEFAULT_NUM_PREDICT))))

    prompt = f"""Anda adalah analis riset ekuitas. Tugas Anda menyusun briefing untuk membantu pemantauan, BUKAN memberi nasihat atau instruksi transaksi.

ATURAN WAJIB:
- Gunakan hanya angka, sinyal, tanggal, dan fakta yang tertulis pada LAPORAN SUMBER. Jangan mencari atau mengarang data eksternal.
- Pertahankan harga, tanggal, mata uang, skor, RSI, Relative Volume, stop, target, dan Risk/Reward persis seperti sumber.
- Jangan mengubah BUY CANDIDATE/WATCH/NO TRADE menjadi perintah beli atau jual.
- Jika data tidak tersedia atau tidak cukup, nyatakan secara terbuka.
- Berikan perhatian khusus pada bagian PANTAUAN KHUSUS TPIA. Jika TPIA berstatus NO_TRADE, jelaskan bahwa status tersebut bukan sinyal untuk masuk posisi.
- Pilih maksimal tiga saham prioritas dari data yang tersedia. Jangan memaksakan pilihan bila tidak ada kandidat.
- Bedakan fakta dari interpretasi. Jangan membuat target harga baru.

FORMAT JAWABAN (Bahasa Indonesia, sekitar 300–350 token, ringkas tetapi lengkap):
1. RINGKASAN PASAR: kondisi umum berdasarkan distribusi sinyal dan kualitas data.
2. PRIORITAS PEMANTAUAN: maksimal tiga saham, alasan, skor, RSI/RelVol dan Risk/Reward bila tersedia.
3. RISIKO UTAMA: risiko teknikal, data, volatilitas, likuiditas, dan hal yang harus diverifikasi.
4. TPIA: status, harga penutupan dan tanggal data, RSI, RelVol, return 5 sesi, serta alasan statusnya.
5. RENCANA SESI BERIKUTNYA: hal konkret yang perlu diamati, tanpa instruksi transaksi.

LAPORAN SUMBER:
{report}
"""
    try:
        payload = _generate(prompt, url, model, timeout, num_predict)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Gagal menghubungi Ollama: {exc}") from exc

    answer = str(payload.get("response", "")).strip()
    # Retry only when Ollama explicitly reports that generation hit its token ceiling.
    if answer and payload.get("done_reason") == "length":
        retry = _generate(prompt, url, model, timeout, max(num_predict + 250, 850))
        answer = str(retry.get("response", answer)).strip()
    if not answer:
        raise RuntimeError("Ollama mengembalikan jawaban kosong.")
    return answer


def enrich_report(report: str) -> str:
    """Append model commentary; preserve deterministic source report unchanged."""
    try:
        commentary = analyze_report(report)
        return (
            report
            + "\n\n🤖 ANALISIS AI LOKAL (OLLAMA / GEMMA)\n"
            + commentary
            + "\n\nCatatan: analisis AI hanya interpretasi atas data sumber; verifikasi angka dan jangan jadikan satu-satunya dasar keputusan."
        )
    except Exception as exc:
        return (
            report
            + "\n\n⚠️ ANALISIS OLLAMA TIDAK TERSEDIA\n"
            + "Laporan data tetap dapat dikirim. Periksa layanan Ollama dan model lokal. "
            + f"Detail: {type(exc).__name__}: {str(exc)[:300]}"
        )
