# AI Employee — Daily Equity Research Telegram Report

## Tugas harian
- Memindai watchlist awal saham IDX dan US dari Yahoo Finance.
- Menghitung indikator teknikal dan mengelompokkan BUY CANDIDATE / WATCH / NO TRADE.
- Menyertakan harga penutupan, tanggal bar, skor, entry indikatif, stop, target, dan risk/reward jika tersedia.
- Menyertakan saham yang gagal diambil datanya agar masalah data tidak tersembunyi.
- Menyimpan hasil scan di SQLite dan mencegah laporan terkirim dua kali pada tanggal yang sama.
- Mengirim laporan ke Telegram chat yang ada di allowlist.

## Instalasi Windows (sekali saja)
1. Ekstrak folder proyek ke komputer Windows.
2. Pastikan Windows menggunakan zona waktu `(UTC+07:00) Bangkok, Hanoi, Jakarta`.
3. Klik kanan `install_daily_employee.ps1` → **Run with PowerShell**. Jika kebijakan Windows memblokir script, buka PowerShell di folder proyek dan jalankan `powershell -ExecutionPolicy Bypass -File .\install_daily_employee.ps1`.
4. Masukkan Telegram Bot Token dan Chat ID ketika diminta. Token disimpan lokal di `.env`, bukan di Git.
5. Installer menguji Telegram lalu membuat jadwal Task Scheduler Senin–Jumat pukul 07:30 WIB.

## Uji manual
- Scan tanpa mengirim: `.venv\Scripts\python.exe daily_signal_scheduler.py --dry-run`
- Kirim laporan sekarang: `.venv\Scripts\python.exe daily_signal_scheduler.py --force`
- Tes koneksi Telegram: `.venv\Scripts\python.exe daily_signal_scheduler.py --test-telegram`

## Syarat agar otomatis
Komputer harus menyala, akun Windows sedang login, dan internet tersedia pada waktu tugas. Task Scheduler memakai zona waktu lokal Windows. Jika ingin berjalan saat komputer mati, proyek perlu dipindahkan ke server/VPS yang selalu aktif.

## Batasan penting
- Watchlist default hanya 15 saham IDX dan 10 simbol US; bukan pemindaian seluruh bursa.
- Sumber harga Yahoo Finance pihak ketiga; bar terakhir dapat tertinggal atau tidak tersedia pada hari libur.
- Sinyal adalah kandidat riset, bukan instruksi transaksi. Sistem tidak terhubung ke broker dan tidak menempatkan order.
- Aturan sinyal masih hipotesis dan harus dinilai melalui backtest, walk-forward, dan paper trading.
- Telegram bot token adalah rahasia. Jangan mengirim `.env` atau mengunggahnya ke GitHub.
