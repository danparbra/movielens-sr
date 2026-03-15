import sqlite3
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent.parent / 'users.db'
USERS_DAT_PATH = Path(__file__).parent.parent.parent / 'artifacts/data/users.dat'


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        gender TEXT,
        age INTEGER,
        occupation INTEGER,
        zipcode TEXT,
        password TEXT
    )''')
    conn.commit()
    conn.close()


def load_users_from_dat(limit: int = 20):
    conn = get_connection()
    c = conn.cursor()
    with open(USERS_DAT_PATH, 'r') as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            parts = line.strip().split('::')
            if len(parts) >= 5:
                user_id, gender, age, occupation, zipcode = parts[:5]
                # Default password is 'password' for demo
                c.execute('INSERT OR IGNORE INTO users (user_id, gender, age, occupation, zipcode, password) VALUES (?, ?, ?, ?, ?, ?)',
                          (int(user_id), gender, int(age), int(occupation), zipcode, 'password'))
    conn.commit()
    conn.close()


def register(userName: str, password: str, gender: str, age: int, occupation: int, zipcode: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (user_id, gender, age, occupation, zipcode, password) VALUES (?, ?, ?, ?, ?, ?)',
                  (userName, gender, age, occupation, zipcode, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login(userName: str, password: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE user_id = ?', (userName,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == password:
        return True
    return False


# Call this on first run to initialize DB and load users
if __name__ == '__main__':
    init_db()
    load_users_from_dat(20)