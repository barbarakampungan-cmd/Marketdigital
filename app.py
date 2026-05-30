from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    g,
    flash
)

import sqlite3
import os

from werkzeug.utils import secure_filename

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)

app.secret_key = "digitalmarket_secret"

DATABASE_NAME = "database/digitalmarket.db"

UPLOAD_FOLDER = "static/uploads"
FILE_FOLDER = "static/files"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["FILE_FOLDER"] = FILE_FOLDER

# ======================================
# CEK USER LOGIN
# ======================================

@app.before_request
def load_logged_in_user():

    g.user = session.get("user_email")

# ======================================
# HOME
# ======================================

@app.route("/")
def home():

    search = request.args.get("search")

    category = request.args.get("category")

    page = request.args.get("page", 1, type=int)

    per_page = 6

    offset = (page - 1) * per_page

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # =========================
    # SEARCH PRODUK
    # =========================

    if search:

        cursor.execute("""
        SELECT * FROM products
        WHERE title LIKE ?
        LIMIT ? OFFSET ?
        """, (
            '%' + search + '%',
            per_page,
            offset
        ))

    elif category:

        cursor.execute("""
        SELECT * FROM products
        WHERE category = ?
        LIMIT ? OFFSET ?
        """, (
            category,
            per_page,
            offset
        ))

    else:

        cursor.execute("""
        SELECT * FROM products
        LIMIT ? OFFSET ?
        """, (
            per_page,
            offset
        ))

    products = cursor.fetchall()

    # =========================
    # TOTAL PRODUK
    # =========================

    cursor.execute("""
    SELECT COUNT(*) FROM products
    """)

    total_products = cursor.fetchone()[0]

    total_pages = (
        total_products + per_page - 1
    ) // per_page

    conn.close()

    return render_template(
        "index.html",
        products=products,
        page=page,
        total_pages=total_pages
    )


# ======================================
# DETAIL PRODUK
# ======================================

@app.route("/product/<int:id>")
def product_detail(id):

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE id = ?
    """, (id,))

    product = cursor.fetchone()

    conn.close()

    return render_template(
        "product_detail.html",
        product=product
    )

# ======================================
# LOGIN
# ======================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = generate_password_hash(
        request.form["password"]
     )

        conn = sqlite3.connect(DATABASE_NAME)

        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM users
        WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(
            user[3],
            password
        ):

            session["user_email"] = email

            return redirect("/dashboard")

        flash("Email atau password salah!")

        return redirect("/login")

    return render_template("login.html")

# ======================================
# REGISTER
# ======================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        password = request.form["password"]

        conn = sqlite3.connect(DATABASE_NAME)

        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO users
            (username, email, password)

            VALUES (?, ?, ?)
            """, (
                username,
                email,
                password
            ))

            conn.commit()

            conn.close()

            flash("Register berhasil! Silakan login.")

            return redirect("/login")

        except:

            conn.close()

            flash("Email sudah digunakan!")

            return redirect("/register")

    return render_template("register.html")

# ======================================
# DASHBOARD
# ======================================

@app.route("/dashboard")
def dashboard():

    if "user_email" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        email=session["user_email"]
    )

# ======================================
# UPLOAD PRODUK
# ======================================

@app.route("/upload-product", methods=["GET", "POST"])
def upload_product():

    if "user_email" not in session:
        return redirect("/login")

    if request.method == "POST":

        title = request.form["title"]

        description = request.form["description"]

        price = request.form["price"]

        category = request.form["category"]

        image = request.files["image"]

        product_file = request.files["file"]

        # =========================
        # SIMPAN GAMBAR
        # =========================

        image_filename = secure_filename(
            image.filename
        )

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            image_filename
        )

        image.save(image_path)

        db_image_path = (
            "/static/uploads/" +
            image_filename
        )

        # =========================
        # SIMPAN FILE DIGITAL
        # =========================

        file_filename = secure_filename(
            product_file.filename
        )

        file_path = os.path.join(
            app.config["FILE_FOLDER"],
            file_filename
        )

        product_file.save(file_path)

        db_file_path = (
            "/static/files/" +
            file_filename
        )

        # =========================
        # SIMPAN DATABASE
        # =========================

        conn = sqlite3.connect(DATABASE_NAME)

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO products
        (
            title,
            description,
            price,
            category,
            image,
            file
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            price,
            category,
            db_image_path,
            db_file_path
        ))

        conn.commit()
        conn.close()

        flash("Produk berhasil diupload!")

        return redirect("/dashboard")

    return render_template(
        "upload_product.html"
    )

# ======================================
# CHECKOUT
# ======================================

@app.route("/checkout/<int:id>")
def checkout(id):

    if "user_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE id = ?
    """, (id,))

    product = cursor.fetchone()

    cursor.execute("""
    INSERT INTO transactions
    (
        user_email,
        product_id,
        product_title,
        price
    )

    VALUES (?, ?, ?, ?)
    """, (
        session["user_email"],
        product["id"],
        product["title"],
        product["price"]
    ))

    conn.commit()
    conn.close()

    flash("Checkout berhasil!")

    return render_template(
        "checkout_success.html",
        product=product
    )

# ======================================
# MY ORDERS
# ======================================

@app.route("/my-orders")
def my_orders():

    if "user_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        transactions.id,
        transactions.product_title,
        transactions.price,
        products.file

    FROM transactions

    JOIN products
    ON transactions.product_id = products.id

    WHERE transactions.user_email = ?
    """, (session["user_email"],))

    orders = cursor.fetchall()

    conn.close()

    return render_template(
        "my_orders.html",
        orders=orders
    )

# ======================================
# ADMIN DASHBOARD
# ======================================

@app.route("/admin")
def admin():

    if "user_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # =========================
    # AMBIL PRODUK
    # =========================

    cursor.execute("""
    SELECT * FROM products
    """)

    products = cursor.fetchall()

    # =========================
    # AMBIL TRANSAKSI
    # =========================

    cursor.execute("""
    SELECT * FROM transactions
    """)

    transactions = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        products=products,
        transactions=transactions
    )

# ======================================
# DELETE PRODUK
# ======================================

@app.route("/delete-product/<int:id>")
def delete_product(id):

    conn = sqlite3.connect(DATABASE_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM products
    WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Produk berhasil dihapus!")

    return redirect("/admin")

# ======================================
# LOGOUT
# ======================================

@app.route("/logout")
def logout():

    session.clear()

    flash("Berhasil logout!")

    return redirect("/login")
    
    # ======================================
# EDIT PRODUK
# ======================================

@app.route("/edit-product/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if "user_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # =========================
    # AMBIL PRODUK
    # =========================

    cursor.execute("""
    SELECT * FROM products
    WHERE id = ?
    """, (id,))

    product = cursor.fetchone()

    # =========================
    # UPDATE PRODUK
    # =========================

    if request.method == "POST":

        title = request.form["title"]

        description = request.form["description"]

        price = request.form["price"]

        category = request.form["category"]

        cursor.execute("""
        UPDATE products

        SET
            title = ?,
            description = ?,
            price = ?,
            category = ?

        WHERE id = ?
        """, (
            title,
            description,
            price,
            category,
            id
        ))

        conn.commit()

        conn.close()

        return redirect("/admin")

    conn.close()

    return render_template(
        "edit_product.html",
        product=product
    )

# ======================================
# RUN APP
# ======================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )