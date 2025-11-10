import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "git-webview.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False # ignore

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT password_hash FROM users WHERE username = ?',
        (username,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return check_password_hash(result[0], password)
    return False

if __name__ == "__main__":
    init_db()

    create_user("admin", "admin") # for now
