import sqlite3

# ADMIN_ID ni bu yerga o'z IDingni yoz (Masalan: 12345678)
ADMIN_ID = 7288739341 

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (username TEXT PRIMARY KEY, votes_count INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes (user_id INTEGER, candidate_username TEXT, PRIMARY KEY (user_id, candidate_username))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel', '@TolibTokyo')")
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "@TolibTokyo"

def set_setting(key, value):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE joined_at >= date('now', '-30 days')")
    monthly = cursor.fetchone()[0]
    conn.close()
    return total, monthly

def get_candidates():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes_count FROM candidates")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def get_top_5():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes_count FROM candidates ORDER BY votes_count DESC LIMIT 5")
    res = cursor.fetchall()
    conn.close()
    return res

init_db()
def get_top_candidates(limit=10):
    """Eng ko'p ovoz olgan nomzodlarni limit bo'yicha qaytaradi"""
    import sqlite3
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Ovozlar soni bo'yicha kamayish tartibida saralaymiz
    cursor.execute("SELECT username, votes_count FROM candidates ORDER BY votes_count DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    conn.close()
    return results
