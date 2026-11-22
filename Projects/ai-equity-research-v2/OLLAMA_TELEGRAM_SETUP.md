# Integrasi Ollama + Telegram

Patch ini menambahkan komentar analisis lokal dari Ollama ke laporan Telegram tanpa mengganti mesin pemindaian saham.

## Pemasangan
1. Tutup jendela CMD yang sedang menjalankan laporan.
2. Ekstrak ZIP patch ini ke folder `Projects\ai-equity-research-v2` yang sama.
3. Jika Windows bertanya, izinkan Replace untuk `daily_signal_scheduler.py` dan `daily_signal_service.py`. File lain ditambahkan; database dan `.env` tidak disertakan/ditimpa.
4. Pastikan Ollama berjalan dan `gemma4:latest` tersedia (`ollama list`).
5. Jalankan `TEST_OLLAMA_TELEGRAM.bat`.

## Pengaturan opsional di `.env`
- `OLLAMA_URL=http://127.0.0.1:11434/api/generate`
- `OLLAMA_MODEL=gemma4:latest`
- `OLLAMA_TIMEOUT_SECONDS=240`

Jika Ollama gagal merespons, laporan data tetap dikirim dan Telegram akan menyertakan status kegagalan analisis AI. Scheduler memakai zona waktu Asia/Singapore; jadwal Windows Task Scheduler tetap mengikuti zona waktu Windows yang terpasang.

Komentar AI dibatasi pada data yang sudah ada di laporan. Model tidak mengambil berita atau data eksternal dan dapat salah menafsirkan; verifikasi sebelum mengambil keputusan investasi.
