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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT UNIQUE NOT NULL,
            owner TEXT NOT NULL
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

# REPO QUERIES

def get_repo_info(repo_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT owner FROM repos WHERE repo_name = ?',
        (repo_name,)
    )
    
    result = cursor.fetchone()
    conn.close()

    if result:
        return {"owner": result[0]}
    return False

def set_repo_owner(repo_name, owner):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # repo info might not exist yet, so check, if not, insert
    cursor.execute('SELECT id FROM repos WHERE repo_name = ?', (repo_name,))
    result = cursor.fetchone()
    if result:
        cursor.execute('UPDATE repos SET owner = ? WHERE repo_name = ?', (owner, repo_name))
    else:
        cursor.execute('INSERT INTO repos (repo_name, owner) VALUES (?, ?)', (repo_name, owner))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

    create_user("admin", "admin") # for now
