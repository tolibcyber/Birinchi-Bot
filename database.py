import sqlite3

ADMIN_ID = "7288739341" # O'z ID raqamingni yoz

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Foydalanuvchilar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT)''')
    # Nomzodlar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates 
                      (username TEXT PRIMARY KEY, votes_count INTEGER DEFAULT 0)''')
    # Ovozlar jadvali (user_id UNIQUE qilingan, bittadan ortiq ovoz berib bo'lmaydi)
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes 
                      (user_id INTEGER PRIMARY KEY, candidate_username TEXT)''')
    # Sozlamalar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                      (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Kanalni saqlash uchun boshlang'ich qiymat
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel', '@your_channel')")
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_top_candidates(limit=5):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, votes_count FROM candidates ORDER BY votes_count DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_candidates():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM candidates")
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def get_setting(key):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_stats():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    return total, total # Hozircha umumiy statistika
