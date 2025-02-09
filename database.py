import sqlite3

# 🔥 ডাটাবেস তৈরি করা
conn = sqlite3.connect("bot_database.db")
cursor = conn.cursor()

# ✅ টেবিল তৈরি করা (যদি না থাকে)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()

# 🔄 নতুন ইউজার যোগ করা (যদি না থাকে)
def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# ➕ কয়েন যোগ করা
def add_coins(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

# 🔄 ইউজারের ব্যালেন্স চেক করা
def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0
