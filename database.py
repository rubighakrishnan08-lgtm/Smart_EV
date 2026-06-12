import sqlite3

def init_db():
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    # Create updated bookings table
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

    conn.commit()
    conn.close()