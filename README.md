# Presensi SMP Muhammadiyah 22 Pamulang

Portal presensi harian guru piket, laporan, hasil belajar, dan akun orang tua.

Live: https://presensi-smpm22.secureserver.web.id

## Stack

- Flask + Gunicorn + PM2
- MySQL / MariaDB
- Jinja templates

## Setup singkat

1. Salin `.env.example` ke `.env` dan isi kredensial.
2. Buat database, lalu import dump:

```bash
mysql -u USER -p < db_presensi_smpm22.sql
```

3. Install dependensi Python dan jalankan app:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Catatan

- File `db_presensi_smpm22.sql` berisi snapshot data produksi (termasuk hash password). Jaga akses repo.
- Jangan commit file `.env`.
