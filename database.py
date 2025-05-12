import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    start_date TEXT,
    last_sent INTEGER DEFAULT 0
)
""")
conn.commit()

def add_user(user_id: int):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, start_date) VALUES (?, ?)", (user_id, datetime.now().isoformat()))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id, start_date, last_sent FROM users")
    return cursor.fetchall()

def update_last_sent(user_id: int, day: int):
    cursor.execute("UPDATE users SET last_sent = ? WHERE user_id = ?", (day, user_id))
    conn.commit()