import discord
import sqlite3
import os
import asyncio

TOKEN = os.environ.get("TOKEN_NU")  # 環境変数からトークンを取得
GUILD_ID = 1223638923566252225  # 取得したいサーバー（ギルド）のID
CHANNEL_ID = 1223884690155634698  # 取得したいチャンネルのID
MESSAGE_LIMIT = 100000  # 取得するメッセージ数（必要に応じて変更）

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

# SQLite データベースの初期化
def init_db():
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT,
            content TEXT,
            timestamp TEXT
        )
        """
    )
    conn.commit()
    conn.close()


async def fetch_messages():
    await client.wait_until_ready()
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ 指定されたサーバー (GUILD_ID={GUILD_ID}) が見つかりません！")
        return

    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ 指定されたチャンネル (CHANNEL_ID={CHANNEL_ID}) が見つかりません！")
        return

    print("✅ メッセージ履歴を取得中... (すべてのメッセージ)")

    conn = sqlite3.connect("messages.db")
    c = conn.cursor()

    count = 0  # 取得したメッセージ数をカウント

    # **全メッセージを取得する**
    async for msg in channel.history(limit=None, oldest_first=True):
        c.execute(
            "INSERT INTO messages (author, content, timestamp) VALUES (?, ?, ?)",
            (str(msg.author), msg.content, str(msg.created_at)),
        )
        count += 1

    conn.commit()
    conn.close()

    print(f"✅ {count} 件のメッセージをデータベースに保存しました！")

    await client.close()  # 取得後にボットを終了


# Bot が起動したときの処理
@client.event
async def on_ready():
    print(f"✅ Bot がログインしました: {client.user}")
    await fetch_messages()  # メッセージ履歴を取得する関数を実行


# 実行
if __name__ == "__main__":
    init_db()  # DBの初期化
    client.run(TOKEN)
