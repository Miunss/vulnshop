"""Buat ulang database dan isi data awal (seed)."""
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "vulnshop.db"

PRODUCTS = [
    ("Kopi Gayo 250g", "Biji kopi arabika Gayo, medium roast.", 85000),
    ("Teh Hijau Premium", "Teh hijau daun utuh, 100 gram.", 45000),
    ("Tumbler Stainless 500ml", "Tahan panas dan dingin hingga 12 jam.", 120000),
    ("Notebook A5 Dotted", "Buku catatan 120 halaman, sampul keras.", 35000),
    ("Mouse Wireless", "Mouse nirkabel 2.4GHz, baterai AA.", 99000),
]

USERS = [
    # (username, email, password, is_admin)
    ("admin", "admin@vulnshop.local", "Adm1n-Local-Only!", 1),
    ("alice", "alice@vulnshop.local", "alice-pass-123", 0),
    ("bob", "bob@vulnshop.local", "bob-pass-456", 0),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    with open("schema.sql") as f:
        conn.executescript(f.read())
    conn.executemany(
        "INSERT INTO products (name, description, price) VALUES (?, ?, ?)", PRODUCTS
    )
    for username, email, pw, is_admin in USERS:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            (username, email, generate_password_hash(pw), is_admin),
        )
    # contoh order & komentar supaya ada data untuk dieksplor nanti
    conn.execute("INSERT INTO orders (user_id, product_id, note) VALUES (2, 1, 'Tolong giling halus')")
    conn.execute("INSERT INTO orders (user_id, product_id, note) VALUES (3, 3, 'Warna hitam')")
    conn.execute("INSERT INTO comments (product_id, user_id, body) VALUES (1, 2, 'Aromanya enak banget!')")
    conn.commit()
    conn.close()
    print("Database siap:", DB_PATH)


if __name__ == "__main__":
    main()
