import sqlite3
import logging
from typing import Optional
from core.config import DB_PATH

logger = logging.getLogger(__name__)

# シングルトン接続管理
_connection: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    """DB接続（シングルトン）を取得する"""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
    return _connection


def db_init():
    """データベースの初期化"""
    logger.info("[DATABASE] データベース初期化を開始します")
    try:
        conn = get_connection()
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
        conn.commit()
        logger.info("[DATABASE] データベースの初期化が成功しました")
    except Exception as e:
        logger.error(f"[DATABASE ERROR] 初期化中にエラーが発生しました: {e}")


def save_message(author: str, content: str, timestamp: str):
    """メッセージの保存"""
    logger.debug(f"[DATABASE] メッセージ保存: {author[:10]}... - {content[:20]}...")
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO messages (author, content, timestamp) VALUES (?, ?, ?)",
            (author, content, timestamp),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"[DATABASE ERROR] メッセージ保存中にエラーが発生しました: {e}")


# TTS Profiles CRUD
def set_user_profile(user_id: str, profile: int):
    """ユーザーのTTSプロファイルを設定（0=デフォルト、1〜3=ユーザー1〜3）"""
    logger.info(f"[DATABASE] TTSプロファイル設定: user_id={user_id}, profile={profile}")
    try:
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO tts_profiles (user_id, profile) VALUES (?, ?)",
            (user_id, profile),
        )
        conn.commit()
    except Exception as e:
        logger.error(
            f"[DATABASE ERROR] TTSプロファイル設定中にエラーが発生しました: {e}"
        )


def get_user_profile(user_id: str) -> Optional[int]:
    """ユーザーのTTSプロファイルを取得（未登録の場合はNone）"""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT profile FROM tts_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return row[0]
        return None
    except Exception as e:
        logger.error(
            f"[DATABASE ERROR] TTSプロファイル取得中にエラーが発生しました: {e}"
        )
        return None


def delete_user_profile(user_id: str):
    """ユーザーのTTSプロファイル割当を削除"""
    logger.info(f"[DATABASE] TTSプロファイル削除: user_id={user_id}")
    try:
        conn = get_connection()
        conn.execute("DELETE FROM tts_profiles WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        logger.error(
            f"[DATABASE ERROR] TTSプロファイル削除中にエラーが発生しました: {e}"
        )


def list_user_profiles() -> list[tuple[str, int]]:
    """全ユーザーのTTSプロファイル割当を取得"""
    try:
        conn = get_connection()
        rows = conn.execute("SELECT user_id, profile FROM tts_profiles").fetchall()
        return [(row[0], row[1]) for row in rows]
    except Exception as e:
        logger.error(
            f"[DATABASE ERROR] TTSプロファイル一覧取得中にエラーが発生しました: {e}"
        )
        return []
