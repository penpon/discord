import sqlite3
from discord.ext import commands


class DB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_init()  # データベース初期化をここで実行

    def db_init(self):
        """データベースを初期化"""
        with sqlite3.connect("messages.db") as conn:
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

    @commands.Cog.listener()
    async def on_message(self, message):
        """Discordのメッセージをデータベースに保存"""
        if message.author.bot:
            return  # ボットのメッセージは無視

        # データベースにメッセージを保存
        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO messages (author, content, timestamp) VALUES (?, ?, ?)",
                (str(message.author), message.content, str(message.created_at)),
            )
            conn.commit()

        await self.bot.process_commands(message)  # コマンドも処理する


# CogsにBotを登録
async def setup(bot):
    await bot.add_cog(DB(bot))
