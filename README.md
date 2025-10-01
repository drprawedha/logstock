# LogStock - Sistem Manajemen Logistik

LogStock adalah aplikasi terminal berbasis Python untuk **manajemen stok barang** yang menggantikan bin card manual. Cocok untuk gudang kecil atau menengah.

---

## Fitur Utama

### 1. Manajemen User
- Login dengan username & password
- Role `admin` dan `staff`
  - **Admin**: tambah/hapus barang, tambah user, lihat aktivitas user
  - **Staff**: input transaksi, cek stok (barcode sementara disable)
- Aktivitas user dicatat otomatis

### 2. Barang & Stok
- Tambah barang dengan nama, satuan, lokasi
- Hapus barang **hanya jika saldo = 0**
- Input transaksi MASUK/KELUAR
- History transaksi untuk semua barang atau per barang

### 3. Barcode & Stiker (sementara disable)
- Generate barcode Code128 untuk setiap barang
- Scan barcode untuk cek stok (disable sementara)
- Cetak stiker ke printer Bluetooth (disable sementara)

### 4. Audit Trail
- Setiap aksi user dicatat
- Bisa dilihat melalui menu **Aktivitas User**

---

## Instalasi

1. Clone repository:
```bash
git clone https://github.com/drprawedha/logstock.git
cd logstock
```
2. Buat virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```

3. Install dependency:
```
pip install -r requirements.txt
```

4. Jalankan aplikasi:
```
python3 app.py
```
### Database

Database SQLite: logistik.db

### Tabel utama:

- User → username, password (hash), role
- Barang → nama, satuan, lokasi, barcode
- Transaksi → barang_id, tanggal, tipe, jumlah, keterangan
- UserActivity → user, tanggal, aktivitas

Catatan: Jika database lama belum ada kolom barcode:
```
ALTER TABLE Barang ADD COLUMN barcode TEXT UNIQUE;
```
### Cara Membuat Admin

Jalankan Python shell atau buat script create_admin.py
```
import sqlite3, hashlib

DB = "logistik.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

username = "admin"
password = "AdminPass123!"
pw_hash = hashlib.sha256(password.encode()).hexdigest()
c.execute("INSERT INTO User (username, password, role) VALUES (?, ?, 'admin')", (username, pw_hash))
conn.commit()
conn.close()
```

Login menggunakan username/password tersebut.

## Catatan
- Barcode & stiker untuk sementara disable.
- Pastikan backup database sebelum melakukan migrasi.
- Password disimpan dalam hash SHA-256 untuk keamanan.
