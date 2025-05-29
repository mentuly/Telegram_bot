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

cursor.execute("""
CREATE TABLE IF NOT EXISTS incomplete_tasks (
    user_id INTEGER,
    day INTEGER,
    PRIMARY KEY (user_id, day)
)
""")
conn.commit()

def mark_incomplete(user_id: int, day: int):
    cursor.execute("INSERT OR IGNORE INTO incomplete_tasks (user_id, day) VALUES (?, ?)", (user_id, day))
    conn.commit()

def mark_complete(user_id: int, day: int):
    cursor.execute("DELETE FROM incomplete_tasks WHERE user_id = ? AND day = ?", (user_id, day))
    conn.commit()

def get_incomplete_tasks(user_id: int):
    cursor.execute("SELECT day FROM incomplete_tasks WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    start_date TEXT,
    last_sent INTEGER DEFAULT 0,
    name TEXT
)
""")
conn.commit()

def update_user_name(user_id: int, name: str):
    cursor.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
    conn.commit()

def delete_user(user_id: int):
    print(f"Видаляємо користувача {user_id} з бази")
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM incomplete_tasks WHERE user_id = ?", (user_id,))
    conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    start_date TEXT,
    last_sent INTEGER DEFAULT 0
)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_names (
    user_id INTEGER PRIMARY KEY,
    name TEXT
)
""")
conn.commit()

def update_user_name(user_id: int, name: str):
    cursor.execute(
        "INSERT INTO user_names (user_id, name) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET name=excluded.name",
        (user_id, name)
    )
    conn.commit()

def get_user_name(user_id: int):
    cursor.execute("SELECT name FROM user_names WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None