"""Cyber Cafe Management System."""

import json
import os
import secrets
import urllib.parse
import urllib.request
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename

def load_local_env(env_path):
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

BASE_DIR = Path(__file__).resolve().parent
load_local_env(BASE_DIR / ".env")

CURRENCY_SYMBOL = "Rs"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_ADMIN_EMAIL = os.environ.get("GOOGLE_ADMIN_EMAIL", "").strip().lower()
PAYMENT_UPI_ID = os.environ.get("PAYMENT_UPI_ID", "your-upi-id@bank")
PAYMENT_RECEIVER = os.environ.get("PAYMENT_RECEIVER", "Cyber Cafe")
PAYMENT_QR_IMAGE_URL = os.environ.get("PAYMENT_QR_IMAGE_URL", "").strip()
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "payments"
ALLOWED_PAYMENT_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

USERS = {
    "admin":  {"password": "admin123",  "role": "admin", "name": "Administrator"},
    "user1":  {"password": "user123",   "role": "user",  "name": "Alex Rivera"},
    "user2":  {"password": "user123",   "role": "user",  "name": "Sam Torres"},
}

HOURLY_RATE = 40

stations = {i: {"id": i, "name": f"PC-{i:02d}", "session": None} for i in range(1, 7)}

retail_items = [
    {"id": 1,  "name": "Print B&W",        "unit": "per page", "price": 5},
    {"id": 2,  "name": "Print Color",       "unit": "per page", "price": 15},
    {"id": 3,  "name": "Scan",              "unit": "per page", "price": 10},
    {"id": 4,  "name": "USB Drive 8GB",     "unit": "piece",    "price": 250},
    {"id": 5,  "name": "Photocard Print",   "unit": "piece",    "price": 50},
    {"id": 6,  "name": "Passbook Update",   "unit": "service",  "price": 20},
    {"id": 7,  "name": "ID Lamination",     "unit": "piece",    "price": 30},
    {"id": 8,  "name": "Rank Card (Game)",  "unit": "piece",    "price": 75},
    {"id": 9,  "name": "Headset Rental",    "unit": "per hour", "price": 20},
    {"id": 10, "name": "CD/DVD Burn",       "unit": "piece",    "price": 60},
]

customers = [
    {"id": 1, "name": "Alex Rivera",  "username": "user1", "total_hours": 120, "total_spent": 5800, "sessions": 45},
    {"id": 2, "name": "Sam Torres",   "username": "user2", "total_hours": 67,  "total_spent": 3200, "sessions": 28},
    {"id": 3, "name": "Jordan Lee",   "username": None,    "total_hours": 34,  "total_spent": 1900, "sessions": 15},
    {"id": 4, "name": "Casey Morgan", "username": None,    "total_hours": 12,  "total_spent": 620,  "sessions": 8},
]

activity_log = [{"time": "00:00", "msg": "System initialized"}]
payment_requests = []

def log_event(msg):
    activity_log.insert(0, {"time": datetime.now().strftime("%H:%M"), "msg": msg})

def google_login_enabled():
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

def google_login_status_message():
    if google_login_enabled():
        return "Google sign-in is ready."
    if GOOGLE_CLIENT_ID and not GOOGLE_CLIENT_SECRET:
        return "Google Client ID is configured. Add GOOGLE_CLIENT_SECRET to enable sign-in."
    return "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET on your machine or hosting platform to enable Google login."

def build_google_redirect_uri():
    return url_for("google_callback", _external=True)

def exchange_google_code(code):
    payload = urllib.parse.urlencode({
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": build_google_redirect_uri(),
        "grant_type": "authorization_code",
    }).encode("utf-8")
    request_obj = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request_obj, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def fetch_google_user_info(access_token):
    request_obj = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(request_obj, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def cart_details(cart_data):
    item_map = {item["id"]: item for item in retail_items}
    items = []
    total = 0
    for entry in cart_data:
        item = item_map.get(entry["id"])
        if not item:
            continue
        subtotal = item["price"] * entry["qty"]
        total += subtotal
        items.append({**item, "qty": entry["qty"], "subtotal": subtotal})
    return items, total

def payment_upload_allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PAYMENT_EXTENSIONS

def build_payment_reference():
    return f"CC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"

def build_payment_qr_url(amount, reference):
    if PAYMENT_QR_IMAGE_URL:
        return PAYMENT_QR_IMAGE_URL

    upi_payload = "upi://pay?" + urllib.parse.urlencode({
        "pa": PAYMENT_UPI_ID,
        "pn": PAYMENT_RECEIVER,
        "am": amount,
        "cu": "INR",
        "tn": f"Order {reference}",
    })
    return "https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({
        "size": "260x260",
        "data": upi_payload,
    })

def get_payment_request(payment_id):
    return next((payment for payment in payment_requests if payment["id"] == payment_id), None)

def payment_summary_counts():
    pending = sum(1 for payment in payment_requests if payment["status"] == "pending")
    verified = sum(1 for payment in payment_requests if payment["status"] == "verified")
    rejected = sum(1 for payment in payment_requests if payment["status"] == "rejected")
    return pending, verified, rejected

def ensure_customer_profile(username, name):
    customer = next((c for c in customers if c.get("username") == username), None)
    if customer:
        return customer

    customer = {
        "id": max((c["id"] for c in customers), default=0) + 1,
        "name": name,
        "username": username,
        "total_hours": 0,
        "total_spent": 0,
        "sessions": 0,
    }
    customers.append(customer)
    log_event(f"Customer profile created - {name}")
    return customer

def login_user(username, role, name):
    session["username"] = username
    session["role"] = role
    session["name"] = name
    session["cart"] = []

@app.context_processor
def inject_template_globals():
    return {
        "currency_symbol": CURRENCY_SYMBOL,
        "google_login_enabled": google_login_enabled(),
        "google_login_status_message": google_login_status_message(),
        "payment_upi_id": PAYMENT_UPI_ID,
        "payment_receiver": PAYMENT_RECEIVER,
    }

def get_rank(hours):
    if hours >= 100: return "Diamond"
    if hours >= 50:  return "Platinum"
    if hours >= 20:  return "Gold"
    if hours >= 5:   return "Silver"
    return "Bronze"

def get_station_display():
    result = []
    for sid, s in stations.items():
        row = {"id": sid, "name": s["name"], "session": None, "pct": 0}
        if s["session"]:
            sess = s["session"]
            rem = max(0, int((sess["end_time"] - datetime.now()).total_seconds()))
            if rem == 0:
                log_event(f"{s['name']} expired — {sess['customer']}")
                stations[sid]["session"] = None
            else:
                row["session"] = {**sess, "remaining": rem,
                    "remaining_fmt": f"{rem//3600:02d}:{(rem%3600)//60:02d}:{rem%60:02d}"}
                row["pct"] = int((1 - rem / (sess["hours"] * 3600)) * 100)
        result.append(row)
    return result

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

def admin_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return redirect(url_for("user_dashboard"))
        return f(*args, **kwargs)
    return dec

@app.route("/", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("admin_dashboard") if session["role"] == "admin" else url_for("user_dashboard"))
    error = None
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd   = request.form.get("password", "").strip()
        user  = USERS.get(uname)
        if user and user["password"] == pwd:
            login_user(uname, user["role"], user["name"])
            log_event(f"Login: {user['name']} ({user['role']})")
            return redirect(url_for("admin_dashboard") if user["role"] == "admin" else url_for("user_dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/login/google")
def login_google():
    if not google_login_enabled():
        flash("Google sign-in is not configured yet.")
        return redirect(url_for("login"))

    state = secrets.token_urlsafe(24)
    session["google_oauth_state"] = state
    query = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": build_google_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    })
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")

@app.route("/auth/google/callback")
def google_callback():
    if not google_login_enabled():
        flash("Google sign-in is not configured yet.")
        return redirect(url_for("login"))

    state = request.args.get("state", "")
    if not state or state != session.pop("google_oauth_state", None):
        flash("Google sign-in failed. Please try again.")
        return redirect(url_for("login"))

    code = request.args.get("code", "")
    if not code:
        flash("Google sign-in was cancelled or failed.")
        return redirect(url_for("login"))

    try:
        token = exchange_google_code(code)
        user_info = fetch_google_user_info(token.get("access_token", ""))
    except Exception:
        flash("Google sign-in could not be completed.")
        return redirect(url_for("login"))

    email = (user_info.get("email") or "").strip().lower()
    name = user_info.get("name") or email or "Google User"
    if not email:
        flash("Google account email is unavailable.")
        return redirect(url_for("login"))

    role = "admin" if GOOGLE_ADMIN_EMAIL and email == GOOGLE_ADMIN_EMAIL else "user"
    login_user(email, role, name)
    ensure_customer_profile(email, name)
    log_event(f"Login: {name} ({role}) via Google")
    return redirect(url_for("admin_dashboard") if role == "admin" else url_for("user_dashboard"))

@app.route("/logout")
def logout():
    log_event(f"Logout: {session.get('name','')}")
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    s_data = get_station_display()
    active = sum(1 for s in s_data if s["session"])
    return render_template("admin.html", page="stations", stations=s_data,
        active=active, free=6-active, hourly_rate=HOURLY_RATE,
        log=activity_log[:20], name=session["name"])

@app.route("/admin/allocate", methods=["POST"])
@admin_required
def allocate():
    sid      = int(request.form["station_id"])
    hours    = int(request.form["hours"])
    customer = request.form["customer"].strip()
    if not customer:
        flash("Customer name required.")
        return redirect(url_for("admin_dashboard"))
    if stations[sid]["session"]:
        flash(f"PC-{sid:02d} is already occupied.")
        return redirect(url_for("admin_dashboard"))
    now = datetime.now()
    stations[sid]["session"] = {"customer": customer, "hours": hours,
        "started_at": now.strftime("%H:%M"),
        "end_time": now + timedelta(hours=hours),
        "charge": hours * HOURLY_RATE}
    log_event(f"PC-{sid:02d} started — {customer} ({hours}h) {CURRENCY_SYMBOL}{hours*HOURLY_RATE}")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/release/<int:sid>")
@admin_required
def release(sid):
    sess = stations[sid]["session"]
    if sess:
        log_event(f"PC-{sid:02d} released — {sess['customer']}")
        stations[sid]["session"] = None
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/pos")
@admin_required
def admin_pos():
    sess_cart = session.get("cart", [])
    full_cart, total = cart_details(sess_cart)
    return render_template("admin.html", page="pos", retail_items=retail_items,
        cart=full_cart, cart_total=total, name=session["name"],
        log=activity_log[:10], stations=[], active=0, free=0, hourly_rate=HOURLY_RATE)

@app.route("/admin/pos/add", methods=["POST"])
@admin_required
def pos_add():
    item_id   = int(request.form["item_id"])
    cart_data = session.get("cart", [])
    for e in cart_data:
        if e["id"] == item_id:
            e["qty"] += 1
            session["cart"] = cart_data
            return redirect(url_for("admin_pos"))
    cart_data.append({"id": item_id, "qty": 1})
    session["cart"] = cart_data
    return redirect(url_for("admin_pos"))

@app.route("/admin/pos/remove/<int:item_id>")
@admin_required
def pos_remove(item_id):
    session["cart"] = [e for e in session.get("cart", []) if e["id"] != item_id]
    return redirect(url_for("admin_pos"))

@app.route("/admin/pos/checkout")
@admin_required
def pos_checkout():
    cart_data = session.get("cart", [])
    if not cart_data:
        return redirect(url_for("admin_pos"))
    full_cart, total = cart_details(cart_data)
    payment_reference = build_payment_reference()
    return render_template("admin.html", page="payment", cart=full_cart,
        cart_total=total, payment_reference=payment_reference,
        payment_qr_url=build_payment_qr_url(total, payment_reference),
        name=session["name"], log=activity_log[:10], stations=[], active=0,
        free=0, hourly_rate=HOURLY_RATE)

@app.route("/admin/pos/payment", methods=["POST"])
@admin_required
def pos_payment_submit():
    cart_data = session.get("cart", [])
    if not cart_data:
        flash("Cart is empty.")
        return redirect(url_for("admin_pos"))

    payer_name = request.form.get("payer_name", "").strip()
    payment_reference = request.form.get("payment_reference", "").strip() or build_payment_reference()
    screenshot = request.files.get("payment_screenshot")

    if not payer_name:
        flash("Payer name is required.")
        return redirect(url_for("pos_checkout"))
    if not screenshot or not screenshot.filename:
        flash("Upload the payment screenshot to continue.")
        return redirect(url_for("pos_checkout"))
    if not payment_upload_allowed(screenshot.filename):
        flash("Only PNG, JPG, JPEG, and WEBP files are allowed.")
        return redirect(url_for("pos_checkout"))

    full_cart, total = cart_details(cart_data)
    ext = screenshot.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{payment_reference.lower()}-{secrets.token_hex(4)}.{ext}")
    save_path = UPLOAD_DIR / filename
    screenshot.save(save_path)

    payment_requests.insert(0, {
        "id": secrets.token_hex(8),
        "reference": payment_reference,
        "payer_name": payer_name,
        "total": total,
        "items": full_cart,
        "status": "pending",
        "created_at": datetime.now().strftime("%d %b %Y %H:%M"),
        "verified_at": None,
        "verified_by": None,
        "screenshot_path": f"uploads/payments/{filename}",
    })

    log_event(f"Payment submitted — {payment_reference} {CURRENCY_SYMBOL}{total}")
    session["cart"] = []
    flash(f"Payment submitted for verification. Ref: {payment_reference}")
    return redirect(url_for("admin_payments"))

@app.route("/admin/payments")
@admin_required
def admin_payments():
    pending, verified, rejected = payment_summary_counts()
    return render_template("admin.html", page="payments", payments=payment_requests,
        pending_payments=pending, verified_payments=verified,
        rejected_payments=rejected, name=session["name"], log=activity_log[:10],
        stations=[], active=0, free=0, hourly_rate=HOURLY_RATE, cart=[], cart_total=0)

@app.route("/admin/payments/<payment_id>/verify", methods=["POST"])
@admin_required
def verify_payment(payment_id):
    payment = get_payment_request(payment_id)
    if not payment:
        flash("Payment request not found.")
        return redirect(url_for("admin_payments"))

    payment["status"] = "verified"
    payment["verified_at"] = datetime.now().strftime("%d %b %Y %H:%M")
    payment["verified_by"] = session["name"]
    log_event(f"Payment verified — {payment['reference']}")
    flash(f"Payment {payment['reference']} verified.")
    return redirect(url_for("admin_payments"))

@app.route("/admin/payments/<payment_id>/reject", methods=["POST"])
@admin_required
def reject_payment(payment_id):
    payment = get_payment_request(payment_id)
    if not payment:
        flash("Payment request not found.")
        return redirect(url_for("admin_payments"))

    payment["status"] = "rejected"
    payment["verified_at"] = datetime.now().strftime("%d %b %Y %H:%M")
    payment["verified_by"] = session["name"]
    log_event(f"Payment rejected — {payment['reference']}")
    flash(f"Payment {payment['reference']} rejected.")
    return redirect(url_for("admin_payments"))

@app.route("/admin/rankings")
@admin_required
def admin_rankings():
    ranked = sorted(customers, key=lambda c: c["total_hours"], reverse=True)
    for i, c in enumerate(ranked):
        c["rank"] = get_rank(c["total_hours"])
        c["position"] = i + 1
    return render_template("admin.html", page="rankings", customers=ranked,
        name=session["name"], log=activity_log[:10],
        stations=[], active=0, free=0, hourly_rate=HOURLY_RATE, cart=[], cart_total=0)

@app.route("/admin/log")
@admin_required
def admin_log():
    return render_template("admin.html", page="log", log=activity_log,
        name=session["name"], stations=[], active=0, free=0, hourly_rate=HOURLY_RATE)

@app.route("/user")
@login_required
def user_dashboard():
    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    s_data  = get_station_display()
    my_cust = next((c for c in customers if c.get("username") == session["username"]), None)
    if my_cust:
        my_cust = {**my_cust, "rank": get_rank(my_cust["total_hours"])}
    return render_template("user.html", name=session["name"],
        free_count=sum(1 for s in s_data if not s["session"]),
        stations=s_data, customer=my_cust,
        retail_items=retail_items, hourly_rate=HOURLY_RATE)

@app.route("/api/stations")
@login_required
def api_stations():
    return jsonify(get_station_display())

if __name__ == "__main__":
    log_event("System started")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"

    print("\n  Cyber Cafe Management System")
    print("  Admin: admin / admin123")
    print("  User:  user1 / user123")
    print(f"  Open:  http://localhost:{port}\n")
    app.run(debug=debug, host=host, port=port)
