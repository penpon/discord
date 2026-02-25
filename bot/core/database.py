import sqlite3
import logging
from typing import Optional
from core.config import DB_PATH

logger = logging.getLogger(__name__)

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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT,
                content TEXT,
                timestamp TEXT
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
