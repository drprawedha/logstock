# ===== IMPORT LIBRARY =====
import os
import sqlite3
from datetime import datetime
import hashlib
# Barcode dan printer dibiarkan import, tapi fungsinya tidak dipanggil
import barcode
from barcode.writer import ImageWriter
from escpos.printer import Serial
from PIL import Image

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ===== KONEKSI DATABASE =====
conn = sqlite3.connect("logistik.db")
c = conn.cursor()

# ===== BUAT TABEL =====
# User
c.execute('''CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin','staff')) NOT NULL DEFAULT 'staff'
)''')

# Barang
c.execute('''CREATE TABLE IF NOT EXISTS Barang (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    satuan TEXT,
    lokasi TEXT,
    barcode TEXT UNIQUE
)''')

# Transaksi
c.execute('''CREATE TABLE IF NOT EXISTS Transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barang_id INTEGER NOT NULL,
    tanggal TEXT NOT NULL,
    tipe TEXT CHECK(tipe IN ('MASUK','KELUAR')) NOT NULL,
    jumlah INTEGER NOT NULL,
    keterangan TEXT,
    FOREIGN KEY(barang_id) REFERENCES Barang(id)
)''')

# UserActivity
c.execute('''CREATE TABLE IF NOT EXISTS UserActivity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    tanggal TEXT NOT NULL,
    aktivitas TEXT NOT NULL
)''')
conn.commit()

# ===== FUNGSI HASH PASSWORD =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ===== FUNGSI LOGIN =====
def login():
    while True:
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        password_hash = hash_password(password)
        c.execute("SELECT role FROM User WHERE username=? AND password=?", (username, password_hash))
        user = c.fetchone()
        if user:
            print(f"Login berhasil. Role: {user[0]}\n")
            return username, user[0]
        else:
            print("Login gagal. Username atau password salah.\n")

# ===== FUNGSI CATAT AKTIVITAS USER =====
def log_user_activity(user, aktivitas):
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO UserActivity (user, tanggal, aktivitas) VALUES (?, ?, ?)", (user, tanggal, aktivitas))
    conn.commit()

# ===== FUNGSI TAMBAH USER (ADMIN) =====
def tambah_user():
    clear_screen()
    username = input("Username baru: ").strip()
    password = input("Password: ").strip()
    role = input("Role (admin/staff): ").strip()
    password_hash = hash_password(password)
    try:
        c.execute("INSERT INTO User (username, password, role) VALUES (?, ?, ?)", (username, password_hash, role))
        conn.commit()
        print(f"User '{username}' berhasil ditambahkan.\n")
        log_user_activity(current_user, f"Tambah user '{username}' dengan role {role}")
    except sqlite3.IntegrityError:
        print("Username sudah ada.\n")

# ===== FUNGSI TAMBAH BARANG =====
def tambah_barang():
    clear_screen()
    nama = input("Nama Barang: ").strip()
    satuan = input("Satuan (pcs/box/kg/lainnya): ").strip()
    lokasi = input("Lokasi Gudang: ").strip()
    
    while True:
        barcode_kode = input("Kode Barcode (unik): ").strip()
        # cek apakah barcode sudah ada
        c.execute("SELECT id FROM Barang WHERE barcode=?", (barcode_kode,))
        if c.fetchone():
            print(f"Kode barcode '{barcode_kode}' sudah ada! Masukkan kode lain.\n")
        else:
            break

    c.execute("INSERT INTO Barang (nama, satuan, lokasi, barcode) VALUES (?, ?, ?, ?)",
              (nama, satuan, lokasi, barcode_kode))
    conn.commit()
    print(f"Barang '{nama}' berhasil ditambahkan dengan barcode '{barcode_kode}'.\n")
    log_user_activity(current_user, f"Tambah barang '{nama}' (barcode {barcode_kode})")


# ===== FUNGSI INPUT TRANSAKSI =====
def input_transaksi():
    clear_screen()
    barang_id = int(input("ID Barang: "))
    tipe = input("Tipe Transaksi (MASUK/KELUAR): ").upper()
    jumlah = int(input("Jumlah: "))
    keterangan = input("Keterangan (opsional): ")
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO Transaksi (barang_id, tanggal, tipe, jumlah, keterangan) VALUES (?, ?, ?, ?, ?)",
              (barang_id, tanggal, tipe, jumlah, keterangan))
    conn.commit()
    c.execute("SELECT nama FROM Barang WHERE id=?", (barang_id,))
    nama_barang = c.fetchone()[0]
    print(f"Transaksi {tipe} {jumlah} unit '{nama_barang}' berhasil dicatat.\n")
    log_user_activity(current_user, f"Transaksi {tipe} {jumlah} '{nama_barang}' ({keterangan})")

# ===== FUNGSI HAPUS BARANG =====
def hapus_barang():
    clear_screen()
    list_barang()
    barang_id = int(input("Masukkan ID barang yang ingin dihapus: "))
    c.execute("SELECT nama FROM Barang WHERE id=?", (barang_id,))
    barang = c.fetchone()
    if not barang:
        print("Barang tidak ditemukan.\n")
        return
    nama = barang[0]
    c.execute("SELECT SUM(CASE WHEN tipe='MASUK' THEN jumlah ELSE -jumlah END) FROM Transaksi WHERE barang_id=?", (barang_id,))
    saldo = c.fetchone()[0] or 0
    if saldo != 0:
        print(f"Barang '{nama}' tidak bisa dihapus karena saldo masih {saldo}.\n")
        return
    c.execute("DELETE FROM Transaksi WHERE barang_id=?", (barang_id,))
    c.execute("DELETE FROM Barang WHERE id=?", (barang_id,))
    conn.commit()
    print(f"Barang '{nama}' berhasil dihapus.\n")
    log_user_activity(current_user, f"Hapus barang '{nama}'")

# ===== FUNGSI LIST BARANG =====
def list_barang():
    clear_screen()
    print("\nDaftar Barang:")
    print(f"{'ID':3} | {'Nama':20} | {'Satuan':6} | {'Lokasi':10} | {'Barcode'}")
    print("-"*70)
    c.execute("SELECT id, nama, satuan, lokasi, barcode FROM Barang")
    for id_, nama, satuan, lokasi, barcode_ in c.fetchall():
        print(f"{id_:3} | {nama:20} | {satuan:6} | {lokasi:10} | {barcode_}")
    print("")

# ===== FUNGSI HISTORY TRANSAKSI =====
def history_transaksi():
    clear_screen()
    print("===== History Transaksi =====")
    print("1. Semua Barang")
    print("2. Berdasarkan Barang")
    choice = input("Pilih opsi (1/2): ").strip()
    if choice == "1":
        c.execute('''SELECT t.id, b.nama, t.tanggal, t.tipe, t.jumlah, t.keterangan
                     FROM Transaksi t
                     JOIN Barang b ON t.barang_id = b.id
                     ORDER BY t.tanggal''')
    elif choice == "2":
        list_barang()
        barang_id = int(input("Masukkan ID barang: "))
        c.execute('''SELECT t.id, b.nama, t.tanggal, t.tipe, t.jumlah, t.keterangan
                     FROM Transaksi t
                     JOIN Barang b ON t.barang_id = b.id
                     WHERE t.barang_id = ?
                     ORDER BY t.tanggal''', (barang_id,))
    else:
        print("Opsi tidak valid.\n")
        return
    rows = c.fetchall()
    if not rows:
        print("Tidak ada transaksi.\n")
        return
    print(f"{'ID':3} | {'Barang':20} | {'Tanggal':19} | {'Tipe':6} | {'Jumlah':6} | Keterangan")
    print("-"*80)
    for tid, nama, tanggal, tipe, jumlah, keterangan in rows:
        print(f"{tid:3} | {nama:20} | {tanggal:19} | {tipe:6} | {jumlah:6} | {keterangan}")
    print("")

# ===== FUNGSI TAMPIL AKTIVITAS USER =====
def tampil_user_activity():
    print("\n===== Aktivitas User =====")
    c.execute("SELECT user, tanggal, aktivitas FROM UserActivity ORDER BY tanggal")
    rows = c.fetchall()
    if not rows:
        print("Belum ada aktivitas.\n")
        return
    print(f"{'User':15} | {'Tanggal':19} | Aktivitas")
    print("-"*70)
    for user, tanggal, aktivitas in rows:
        print(f"{user:15} | {tanggal:19} | {aktivitas}")
    print("")

# ===== LOGIN =====
current_user, current_role = login()



# ===== MENU INTERAKTIF =====
def main_menu():
    while True:
        print("===== LogStock Lengkap (Barcode & Stiker DISABLE) =====")
        print("1. Tambah Barang (admin)")
        print("2. Input Transaksi")
        print("3. List Barang")
        print("4. Hapus Barang (admin)")
        print("5. History Transaksi")
        print("6. Tambah User (admin)")
        print("7. Aktivitas User (admin)")
        print("8. Keluar")
        choice = input("Pilih opsi (1-8): ").strip()
        print("")

        if choice == "1" and current_role=="admin":
            tambah_barang()
        elif choice == "2":
            input_transaksi()
        elif choice == "3":
            list_barang()
        elif choice == "4" and current_role=="admin":
            hapus_barang()
        elif choice == "5":
            history_transaksi()
        elif choice == "6" and current_role=="admin":
            tambah_user()
        elif choice == "7" and current_role=="admin":
            tampil_user_activity()
        elif choice == "8":
            print("Keluar dari program.")
            break
        else:
            print("Opsi tidak valid atau tidak diperbolehkan untuk role Anda.\n")

# ===== JALANKAN MENU =====
if __name__ == "__main__":
    main_menu()
    conn.close()
