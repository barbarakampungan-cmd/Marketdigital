import sqlite3

# =========================
# NAMA DATABASE
# =========================

DATABASE_NAME = "digitalmarket.db"

# =========================
# CONNECT DATABASE
# =========================

conn = sqlite3.connect(DATABASE_NAME)

cursor = conn.cursor()

# =========================
# TABLE PRODUCTS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    description TEXT NOT NULL,

    price TEXT,

    category TEXT,

    image TEXT,

    file TEXT

)
""")

# =========================
# TABLE USERS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,

    email TEXT NOT NULL UNIQUE,

    password TEXT NOT NULL

)
""")

# =========================
# TABLE TRANSACTIONS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_email TEXT,

    product_id INTEGER,

    product_title TEXT,

    price TEXT

)
""")

# =========================
# SIMPAN DATABASE
# =========================

conn.commit()

conn.close()

print("Database berhasil dibuat!")