# config.py
import os
import re

print("[CONFIG] 設定ファイルを読み込み中...")

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
