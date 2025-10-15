# database.py
import sqlite3
from typing import Optional

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
            c.execute("""
                CREATE TABLE IF NOT EXISTS tts_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile INTEGER NOT NULL
                )
            """)
            c.execute("DELETE FROM tts_profiles WHERE profile IN (4,5)")
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


# TTS Profiles CRUD
def set_user_profile(user_id: str, profile: int):
    """ユーザーのTTSプロファイルを設定（0=デフォルト、1〜5=ユーザー1〜5）"""
    print(f"[DATABASE] TTSプロファイル設定を試行: user_id={user_id}, profile={profile}")
    try:
        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO tts_profiles (user_id, profile)
                VALUES (?, ?)
            """, (user_id, profile))
            conn.commit()
        print(f"[DATABASE] TTSプロファイルの設定に成功しました")
    except Exception as e:
        print(f"[DATABASE ERROR] TTSプロファイル設定中にエラーが発生しました: {str(e)}")


def get_user_profile(user_id: str) -> Optional[int]:
    """ユーザーのTTSプロファイルを取得（未登録の場合はNone）"""
    try:
        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute("SELECT profile FROM tts_profiles WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            if result:
                print(f"[DATABASE] TTSプロファイル取得成功: user_id={user_id}, profile={result[0]}")
                return result[0]
            else:
                print(f"[DATABASE] TTSプロファイル未登録: user_id={user_id}")
                return None
    except Exception as e:
        print(f"[DATABASE ERROR] TTSプロファイル取得中にエラーが発生しました: {str(e)}")
        return None


def delete_user_profile(user_id: str):
    """ユーザーのTTSプロファイル割当を削除"""
    print(f"[DATABASE] TTSプロファイル削除を試行: user_id={user_id}")
    try:
        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute("DELETE FROM tts_profiles WHERE user_id = ?", (user_id,))
            conn.commit()
        print(f"[DATABASE] TTSプロファイルの削除に成功しました")
    except Exception as e:
        print(f"[DATABASE ERROR] TTSプロファイル削除中にエラーが発生しました: {str(e)}")


def list_user_profiles() -> list[tuple[str, int]]:
    """全ユーザーのTTSプロファイル割当を取得"""
    print(f"[DATABASE] 全TTSプロファイル一覧を取得中...")
    try:
        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, profile FROM tts_profiles")
            results = c.fetchall()
        print(f"[DATABASE] TTSプロファイル一覧取得成功: {len(results)}件")
        return results
    except Exception as e:
        print(f"[DATABASE ERROR] TTSプロファイル一覧取得中にエラーが発生しました: {str(e)}")
        return []
