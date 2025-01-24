# database.py
import sqlite3

def db_init():
    """データベースの初期化"""
    print("[DATABASE] データベース初期化を開始します")
    try:
        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT,
                    content TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()
        print("[DATABASE] データベースの初期化が成功しました")
    except Exception as e:
        print(f"[DATABASE ERROR] 初期化中にエラーが発生しました: {str(e)}")

def save_message(author: str, content: str, timestamp: str):
    """メッセージの保存"""
    print(f"[DATABASE] メッセージ保存を試行します: {author[:10]}... - {content[:20]}...")
    try:
        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO messages (author, content, timestamp)
                VALUES (?, ?, ?)
            """, (author, content, timestamp))
            conn.commit()
        print("[DATABASE] メッセージの保存に成功しました")
    except Exception as e:
        print(f"[DATABASE ERROR] メッセージ保存中にエラーが発生しました: {str(e)}")
