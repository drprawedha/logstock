import sqlite3
from datetime import datetime

# ===== Koneksi database =====
conn = sqlite3.connect("logistik.db")
c = conn.cursor()

# ===== Buat tabel jika belum ada =====
c.execute('''CREATE TABLE IF NOT EXISTS Barang (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                satuan TEXT,
                lokasi TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS Transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barang_id INTEGER NOT NULL,
                tanggal TEXT NOT NULL,
                tipe TEXT CHECK(tipe IN ('MASUK','KELUAR')) NOT NULL,
                jumlah INTEGER NOT NULL,
                keterangan TEXT,
                FOREIGN KEY(barang_id) REFERENCES Barang(id)
            )''')

conn.commit()

# ===== Fungsi tambah barang =====
def tambah_barang():
    nama = input("Nama Barang: ")
    satuan = input("Satuan (pcs/box/kg/lainnya): ")
    lokasi = input("Lokasi Gudang: ")
    c.execute("INSERT INTO Barang (nama, satuan, lokasi) VALUES (?, ?, ?)", (nama, satuan, lokasi))
    conn.commit()
    print(f"Barang '{nama}' berhasil ditambahkan.\n")

# ===== Fungsi input transaksi =====
def input_transaksi():
    barang_id = int(input("ID Barang: "))
    tipe = input("Tipe Transaksi (MASUK/KELUAR): ").upper()
    if tipe not in ["MASUK", "KELUAR"]:
        print("Tipe transaksi harus MASUK atau KELUAR.\n")
        return
    jumlah = int(input("Jumlah: "))
    keterangan = input("Keterangan (opsional): ")
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO Transaksi (barang_id, tanggal, tipe, jumlah, keterangan) VALUES (?, ?, ?, ?, ?)",
              (barang_id, tanggal, tipe, jumlah, keterangan))
    conn.commit()
    print(f"Transaksi {tipe} {jumlah} unit berhasil dicatat.\n")

# ===== Fungsi tampil bin card =====
def tampil_bin_card():
    barang_id = int(input("ID Barang: "))
    c.execute("SELECT nama, satuan FROM Barang WHERE id=?", (barang_id,))
    barang = c.fetchone()
    if not barang:
        print("Barang tidak ditemukan.\n")
        return
    nama, satuan = barang
    print(f"\nBin Card: {nama} ({satuan})")
    print(f"{'Tanggal':20} | {'Tipe':6} | {'Jumlah':6} | {'Saldo':6} | Keterangan")
    print("-"*70)
    c.execute("SELECT tanggal, tipe, jumlah, keterangan FROM Transaksi WHERE barang_id=? ORDER BY tanggal", (barang_id,))
    saldo = 0
    for tanggal, tipe, jumlah, keterangan in c.fetchall():
        if tipe == "MASUK":
            saldo += jumlah
        else:
            saldo -= jumlah
        print(f"{tanggal:20} | {tipe:6} | {jumlah:6} | {saldo:6} | {keterangan}")
    print("")

# ===== Fungsi list barang =====
def list_barang():
    print("\nDaftar Barang:")
    print(f"{'ID':3} | {'Nama':20} | {'Satuan':6} | {'Lokasi'}")
    print("-"*50)
    c.execute("SELECT id, nama, satuan, lokasi FROM Barang")
    for id_, nama, satuan, lokasi in c.fetchall():
        print(f"{id_:3} | {nama:20} | {satuan:6} | {lokasi}")
    print("")

# ===== Menu Interaktif =====
def main_menu():
    while True:
        print("===== Sistem Logistik Bin Card Digital =====")
        print("1. Tambah Barang")
        print("2. Input Transaksi")
        print("3. Lihat Bin Card")
        print("4. List Barang")
        print("5. Keluar")
        choice = input("Pilih opsi (1-5): ")
        print("")
        if choice == "1":
            tambah_barang()
        elif choice == "2":
            input_transaksi()
        elif choice == "3":
            tampil_bin_card()
        elif choice == "4":
            list_barang()
        elif choice == "5":
            print("Keluar dari program.")
            break
        else:
            print("Opsi tidak valid.\n")

if __name__ == "__main__":
    main_menu()
    conn.close()
