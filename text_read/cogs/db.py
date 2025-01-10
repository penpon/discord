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
        """Discordのメッセージをデータベースに保存（データをprintする）"""
        if message.author.bot:
            return  # ボットのメッセージは無視

        author = str(message.author)
        content = message.content
        timestamp = str(message.created_at)

        # 追加: 保存するデータをprint
        print(f"保存するデータ: author={author}, content={content}, timestamp={timestamp}")

        with sqlite3.connect("messages.db") as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO messages (author, content, timestamp)
                VALUES (?, ?, ?)
                """,
                (author, content, timestamp),
            )
            conn.commit()

        await self.bot.process_commands(message)  # コマンドも処理する


# CogsにBotを登録
async def setup(bot):
    await bot.add_cog(DB(bot))
