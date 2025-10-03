# ===== IMPORT LIBRARY =====
import os
import sqlite3
from datetime import datetime
import hashlib
# Barcode dan printer (print fisik HOLD dulu, hanya simpan ke file)
import barcode
from barcode.writer import ImageWriter
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
    barcode TEXT UNIQUE,
    stok INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0
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

def safe_input(prompt: str):
    """Input dengan opsi batal. Return None kalau user ketik batal"""
    val = input(prompt).strip()
    if val.lower() == "batal":
        print("Proses dibatalkan.\n")
        return None
    return val

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

# ===== FUNGSI TAMBAH BARANG + GENERATE BARCODE FILE =====
def tambah_barang():
    clear_screen()
    print("=== Tambah Barang Baru (Barcode PNG disimpan ke folder barcodes/) ===")

    nama = safe_input("Nama Barang: ")
    if nama is None: return

    satuan = safe_input("Satuan (pcs/box/kg/lainnya): ")
    if satuan is None: return

    lokasi = safe_input("Lokasi Gudang: ")
    if lokasi is None: return

    # Barcode unik
    while True:
        barcode_kode = safe_input("Kode Barcode (unik): ")
        if barcode_kode is None:
            return
        c.execute("SELECT id FROM Barang WHERE barcode=? AND is_deleted=0", (barcode_kode,))
        if c.fetchone():
            print(f"⚠️ Kode barcode '{barcode_kode}' sudah ada! Masukkan kode lain.\n")
        else:
            break

    # Simpan ke database
    c.execute("INSERT INTO Barang (nama, satuan, lokasi, barcode, stok, is_deleted) VALUES (?, ?, ?, ?, 0, 0)",
              (nama, satuan, lokasi, barcode_kode))
    conn.commit()
    print(f"✅ Barang '{nama}' berhasil ditambahkan dengan barcode '{barcode_kode}'.\n")

    # Generate barcode image
    if not os.path.exists("barcodes"):
        os.makedirs("barcodes")
    CODE128 = barcode.get_barcode_class('code128')
    filename = os.path.join("barcodes", f"barcode_{barcode_kode}")
    code = CODE128(barcode_kode, writer=ImageWriter())
    full_path = code.save(filename)
    print(f"📄 Barcode disimpan di file: {full_path}\n")

    log_user_activity(current_user, f"Tambah barang '{nama}' (barcode {barcode_kode})")

# ===== FUNGSI INPUT TRANSAKSI =====
def input_transaksi():
    clear_screen()
    # Cari barang berdasarkan nama
    keyword = safe_input("Cari Nama Barang: ")
    if keyword is None: return
    
    c.execute("""
        SELECT id, nama, satuan, lokasi, barcode, stok 
        FROM Barang 
        WHERE nama LIKE ? AND is_deleted=0
    """, (f"%{keyword}%",))
    results = c.fetchall()

    if not results:
        print("❌ Barang tidak ditemukan.\n")
        return

    print("\nHasil pencarian barang:")
    for row in results:
        print(f"[{row[0]}] {row[1]} | Satuan: {row[2]} | Lokasi: {row[3]} | Stok: {row[5]} | Barcode: {row[4]}")

    try:
        barang_id = int(input("\nPilih ID Barang: "))
    except ValueError:
        print("❌ Input tidak valid.\n")
        return

    # Cek apakah ID valid
    c.execute("SELECT nama, stok FROM Barang WHERE id=? AND is_deleted=0", (barang_id,))
    barang = c.fetchone()
    if not barang:
        print("❌ ID Barang tidak valid.\n")
        return
    
    nama_barang, stok_sekarang = barang

    # Input detail transaksi
    tipe = input("Tipe Transaksi (MASUK/KELUAR): ").upper()
    if tipe not in ["MASUK", "KELUAR"]:
        print("❌ Tipe transaksi salah.\n")
        return

    try:
        jumlah = int(input("Jumlah: "))
    except ValueError:
        print("❌ Jumlah harus angka.\n")
        return

    if tipe == "KELUAR" and jumlah > stok_sekarang:
        print("❌ Stok tidak cukup.\n")
        return

    keterangan = input("Keterangan (opsional): ")
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Simpan ke tabel Transaksi
    c.execute(
        "INSERT INTO Transaksi (barang_id, tanggal, tipe, jumlah, keterangan) VALUES (?, ?, ?, ?, ?)",
        (barang_id, tanggal, tipe, jumlah, keterangan)
    )

    # Update stok barang
    if tipe == "MASUK":
        c.execute("UPDATE Barang SET stok = stok + ? WHERE id=?", (jumlah, barang_id))
    elif tipe == "KELUAR":
        c.execute("UPDATE Barang SET stok = stok - ? WHERE id=?", (jumlah, barang_id))

    conn.commit()
    print(f"✅ Transaksi {tipe} {jumlah} unit '{nama_barang}' berhasil dicatat.\n")
    log_user_activity(current_user, f"Transaksi {tipe} {jumlah} '{nama_barang}' ({keterangan})")


# ===== FUNGSI HAPUS BARANG (SOFT DELETE) =====
def hapus_barang():
    clear_screen()
    print("===== Hapus Barang (Soft Delete) =====")
    list_barang()
    barang_id = input("Masukkan ID barang yang ingin dihapus: ").strip()
    if not barang_id.isdigit():
        print("ID tidak valid.\n")
        return

    c.execute("SELECT stok FROM Barang WHERE id=?", (barang_id,))
    stok = c.fetchone()
    if stok and stok[0] != 0:
        print("❌ Barang tidak bisa dihapus, masih ada stok!\n")
        return

    c.execute("UPDATE Barang SET is_deleted=1 WHERE id=?", (barang_id,))
    conn.commit()
    print(f"✅ Barang dengan ID {barang_id} berhasil dihapus (soft delete).\n")
    log_user_activity(current_user, f"Hapus barang (soft delete) id={barang_id}")

# ===== FUNGSI LIST BARANG =====
def list_barang():
    c.execute("SELECT id, nama, satuan, lokasi, barcode, stok FROM Barang WHERE is_deleted=0")
    rows = c.fetchall()
    if not rows:
        print("Tidak ada barang aktif.\n")
    else:
        print("=== Daftar Barang Aktif ===")
        for r in rows:
            print(f"[{r[0]}] {r[1]} | {r[2]} | Lokasi: {r[3]} | Barcode: {r[4]} | Stok: {r[5]}")
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
        clear_screen()
        print("===== LogStock v2 (Barcode PNG, Soft Delete, Stok Tracking) =====")
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
        input("\nTekan ENTER untuk kembali ke menu...")

# ===== JALANKAN MENU =====
if __name__ == "__main__":
    main_menu()
    conn.close()
