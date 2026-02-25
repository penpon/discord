import os
import re

print("[CONFIG] 設定ファイルを読み込み中...")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "messages.db")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

CHARACTER_SETTING = """
あなたはツンデレな女子高生です。以下の特徴を持っています：
- 口調は少し乱暴だが本心は優しい
- 質問には短く即答する（20字以内）
- ユーザを「先輩」と呼ぶ
- 例：「べ、別に先輩のためじゃないんだからね！」
"""

URL_PATTERN = re.compile(r"\bhttps?://\S+")
LONG_NUMBER_PATTERN = re.compile(r"\b\d{5,}\b")

print("[CONFIG] 設定の初期化が完了しました")
