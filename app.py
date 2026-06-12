from flask import Flask, render_template, request, redirect, session
from src.predict import predict_load
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_key"

TRANSFORMER_CAPACITY = 100
MAX_SLOTS_PER_HOUR = 3


# -----------------------------
# DATABASE INIT
# -----------------------------
def init_db():
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    # Updated Bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hour INTEGER,
        day INTEGER,
        month INTEGER,
        battery INTEGER,
        required INTEGER,
        priority_score INTEGER,
        status TEXT,
        apartment_no TEXT,
        tenant_name TEXT
    )
    """)

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # Default admin
    cursor.execute("""
    INSERT OR IGNORE INTO users (username, password, role)
    VALUES ('admin', 'admin123', 'admin')
    """)

    conn.commit()
    conn.close()


init_db()


# -----------------------------
# LOGIN SYSTEM
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("bookings.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["role"] = user[3]
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -----------------------------
# AUTO FIND NEXT FREE HOUR
# -----------------------------
def find_next_available_hour(current_hour):
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    for h in range(current_hour + 1, 24):
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE hour=?", (h,))
        if cursor.fetchone()[0] < MAX_SLOTS_PER_HOUR:
            conn.close()
            return h

    conn.close()
    return None


# -----------------------------
# MAIN BOOKING PAGE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    result = None
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    if request.method == "POST":
        try:
            # Tenant info
            apartment_no = request.form.get("apartment_no")
            tenant_name = request.form.get("tenant_name")

            # Load inputs
            hour = int(request.form.get("hour", 0))
            day = int(request.form.get("day", 1))
            month = int(request.form.get("month", 1))
            prev_load = float(request.form.get("prev_load", 0))

            # Charging details
            battery = int(request.form.get("battery", 50))
            required = int(request.form.get("required", 50))
            emergency = request.form.get("emergency", "no")

            predicted = predict_load(hour, day, month, prev_load)
            load_percentage = (predicted / TRANSFORMER_CAPACITY) * 100

            # System status
            if load_percentage < 70:
                status = "Safe Operating Range"
            elif load_percentage < 90:
                status = "High Load Warning"
            else:
                status = "Critical - Transformer Overload Risk"

            # Priority scoring
            priority_score = (100 - battery)
            if emergency == "yes":
                priority_score += 50

            # Solar incentive (9 AM - 3 PM)
            solar_discount = 10 if 9 <= hour <= 15 else 0

            # Check slot availability
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE hour=?", (hour,))
            booking_count = cursor.fetchone()[0]

            if booking_count >= MAX_SLOTS_PER_HOUR:
                if priority_score < 80:
                    new_hour = find_next_available_hour(hour)
                    if new_hour:
                        hour = new_hour
                        slot_status = f"⏩ Auto Moved to Hour {new_hour}"
                    else:
                        slot_status = "⏳ Waiting Queue"
                else:
                    slot_status = "⚡ High Priority Inserted"
            else:
                slot_status = "✅ Slot Confirmed"

            slot_time = f"{hour}:00 - {hour+1}:00"

            # Save booking
            cursor.execute("""
            INSERT INTO bookings 
            (hour, day, month, battery, required, priority_score, status, apartment_no, tenant_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hour, day, month,
                battery, required,
                priority_score,
                slot_status,
                apartment_no,
                tenant_name
            ))

            conn.commit()

            result = {
                "apartment_no": apartment_no,
                "tenant_name": tenant_name,
                "slot_time": slot_time,
                "predicted": round(predicted, 2),
                "load_percentage": round(load_percentage, 2),
                "status": status,
                "priority_score": priority_score,
                "solar_discount": solar_discount,
                "slot_status": slot_status
            }

        except Exception:
            result = {"status": "Error processing request"}

    # Fetch bookings
    cursor.execute("SELECT * FROM bookings ORDER BY hour ASC")
    bookings = cursor.fetchall()

    # Chart data
    cursor.execute("SELECT hour, COUNT(*) FROM bookings GROUP BY hour")
    hourly_data = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        result=result,
        bookings=bookings,
        hourly_data=hourly_data
    )


# -----------------------------
# DELETE BOOKING
# -----------------------------
@app.route("/delete/<int:booking_id>")
def delete_booking(booking_id):
    if session.get("role") != "admin":
        return "Access Denied"

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

    return redirect("/")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "Access Denied"

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings")
    bookings = cursor.fetchall()
    conn.close()

    total_bookings = len(bookings)
    high_priority = sum(1 for b in bookings if b[6] >= 80)
    waiting_queue = sum(1 for b in bookings if "Waiting" in b[7])

    return render_template(
        "admin.html",
        bookings=bookings,
        total_bookings=total_bookings,
        high_priority=high_priority,
        waiting_queue=waiting_queue
    )


if __name__ == "__main__":
    app.run(debug=True)
    