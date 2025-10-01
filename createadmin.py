import sqlite3
import hashlib

DB = "logistik.db"

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def create_admin(username, password):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    pw_hash = hash_password(password)
    try:
        c.execute("INSERT INTO User (username, password, role) VALUES (?, ?, 'admin')", (username, pw_hash))
        conn.commit()
        print(f"Admin '{username}' berhasil dibuat.")
    except sqlite3.IntegrityError:
        print(f"Username '{username}' sudah ada. Gunakan reset_password() untuk mengganti password.")
    conn.close()

def reset_password(username, new_password):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    pw_hash = hash_password(new_password)
    c.execute("UPDATE User SET password=? WHERE username=?", (pw_hash, username))
    if c.rowcount == 0:
        print(f"User '{username}' tidak ditemukan.")
    else:
        conn.commit()
        print(f"Password user '{username}' berhasil direset.")
    conn.close()

if __name__ == "__main__":
    # contoh: ubah sesuai keinginan
    create_admin("admin", "AdminPass123!")         # membuat admin baru (jika belum ada)
    # reset_password("admin", "PasswordBaru123!")  # atau pakai reset
