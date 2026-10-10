# VulnShop

Aplikasi web e-commerce mini untuk belajar keamanan aplikasi web (Python, Flask, SQLite).

> ⚠️ Proyek edukasi. Jalankan hanya di komputer lokal (127.0.0.1). Jangan deploy ke internet.

## Status
- [x] Baseline (versi bersih, branch `main`, tag `v0-baseline`)
- [ ] Versi rentan (branch `vulnerable`)
- [ ] Eksploitasi dan dokumentasi PoC
- [ ] Versi aman (branch `secure`)
- [ ] Laporan pentest

## Menjalankan
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
python app.py   # http://127.0.0.1:5000
```

Akun contoh: `alice` / `alice-pass-123`, `bob` / `bob-pass-456`.
