"""VulnShop - BASELINE (versi bersih).

Ini titik awal sebelum kerentanan ditanam. Baseline ini sengaja dibuat benar:
query terparameterisasi, autoescape Jinja2, hash password, cek kepemilikan,
dan CSRF token. Di tahap berikutnya, kontrol-kontrol ini dilemahkan satu per satu.
"""
import secrets
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = "vulnshop.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "ganti-ini-untuk-lab-lokal"  # lab lokal saja


# ---------- Database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------- Auth helpers ----------
def current_user():
    uid = session.get("user_id")
    if uid is None:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Silakan login dulu.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------- CSRF (baseline: aktif untuk semua POST) ----------
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("csrf_token")
        if not token or token != request.form.get("csrf_token"):
            abort(400, "CSRF token tidak valid")


@app.context_processor
def inject_globals():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return {"csrf_token": session["csrf_token"], "user": current_user()}


# ---------- Routes ----------
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        products = db.execute(
            "SELECT * FROM products WHERE name LIKE ?", (f"%{q}%",)
        ).fetchall()
    else:
        products = db.execute("SELECT * FROM products").fetchall()
    return render_template("index.html", products=products, q=q)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or len(password) < 8:
            flash("Isi semua kolom; password minimal 8 karakter.")
            return render_template("register.html")
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Username sudah dipakai.")
            return render_template("register.html")
        flash("Registrasi berhasil, silakan login.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["user_id"] = row["id"]
            return redirect(url_for("index"))
        flash("Username atau password salah.")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product(product_id):
    db = get_db()
    item = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if item is None:
        abort(404)
    if request.method == "POST":
        if current_user() is None:
            return redirect(url_for("login"))
        body = request.form.get("body", "").strip()
        if body:
            db.execute(
                "INSERT INTO comments (product_id, user_id, body) VALUES (?, ?, ?)",
                (product_id, session["user_id"], body),
            )
            db.commit()
        return redirect(url_for("product", product_id=product_id))
    comments = db.execute(
        "SELECT c.body, c.created_at, u.username FROM comments c "
        "JOIN users u ON u.id = c.user_id WHERE c.product_id = ? ORDER BY c.id DESC",
        (product_id,),
    ).fetchall()
    return render_template("product.html", item=item, comments=comments)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/profile/email", methods=["POST"])
@login_required
def change_email():
    email = request.form.get("email", "").strip()
    if email:
        db = get_db()
        db.execute("UPDATE users SET email = ? WHERE id = ?", (email, session["user_id"]))
        db.commit()
        flash("Email diperbarui.")
    return redirect(url_for("profile"))


@app.route("/order/new/<int:product_id>", methods=["POST"])
@login_required
def new_order(product_id):
    db = get_db()
    if db.execute("SELECT 1 FROM products WHERE id = ?", (product_id,)).fetchone() is None:
        abort(404)
    note = request.form.get("note", "").strip()
    cur = db.execute(
        "INSERT INTO orders (user_id, product_id, note) VALUES (?, ?, ?)",
        (session["user_id"], product_id, note),
    )
    db.commit()
    return redirect(url_for("order_detail", order_id=cur.lastrowid))


@app.route("/orders")
@login_required
def orders():
    rows = get_db().execute(
        "SELECT o.id, o.created_at, p.name FROM orders o "
        "JOIN products p ON p.id = o.product_id WHERE o.user_id = ? ORDER BY o.id DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("orders.html", orders=rows)


@app.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    row = get_db().execute(
        "SELECT o.*, p.name, p.price FROM orders o "
        "JOIN products p ON p.id = o.product_id WHERE o.id = ?",
        (order_id,),
    ).fetchone()
    if row is None:
        abort(404)
    if row["user_id"] != session["user_id"]:  # cek kepemilikan (baseline)
        abort(403)
    return render_template("order_detail.html", order=row)


if __name__ == "__main__":
    # Lab lokal: jangan bind ke 0.0.0.0 dan jangan deploy ke internet.
    app.run(host="127.0.0.1", port=5000, debug=False)
