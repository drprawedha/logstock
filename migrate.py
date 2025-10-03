import sqlite3

# path ke database kamu
DB_PATH = "logistik.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1️⃣ Tambahkan kolom stok kalau belum ada
try:
    c.execute("ALTER TABLE Barang ADD COLUMN stok INTEGER DEFAULT 0")
    print("✅ Kolom 'stok' berhasil ditambahkan.")
except sqlite3.OperationalError:
    print("ℹ️ Kolom 'stok' sudah ada, lewati.")

# 2️⃣ Tambahkan kolom is_deleted untuk soft delete
try:
    c.execute("ALTER TABLE Barang ADD COLUMN is_deleted INTEGER DEFAULT 0")
    print("✅ Kolom 'is_deleted' berhasil ditambahkan.")
except sqlite3.OperationalError:
    print("ℹ️ Kolom 'is_deleted' sudah ada, lewati.")

# 3️⃣ Update barang lama supaya stok tidak NULL
c.execute("UPDATE Barang SET stok = 0 WHERE stok IS NULL")
conn.commit()

print("✅ Migrasi selesai. Database siap digunakan!")

conn.close()
