from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from gtts import gTTS
import re
import io
from asyncio import Queue
import asyncio
import sqlite3


class TTSandDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.audio_queue = Queue()
        self.check_voice_channel.start()
        self.db_init()

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

    @commands.command(name="join")
    async def join(self, ctx):
        """ボイスチャンネルに参加します"""
        self.voice_channel = ctx.author.voice.channel
        if self.voice_channel and not ctx.voice_client:
            await self.voice_channel.connect()

    @commands.command(name="leave")
    async def leave(self, ctx):
        """ボイスチャンネルから切断します"""
        if ctx.voice_client:
            try:
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                while not self.audio_queue.empty():
                    await self.audio_queue.get()

                await ctx.voice_client.disconnect()

                if ctx.voice_client:
                    try:
                        ctx.voice_client.cleanup()
                    except Exception as e:
                        print(f"Error during cleanup: {e}")
            except Exception as e:
                print(f"Error during disconnect: {e}")
            finally:
                self.voice_channel = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # "$"から始まるメッセージを無視
        if message.content.startswith("$"):
            print(f"Ignoring message starting with $: {message.content}")
            return

        if re.search(r"\b\d{5,}\b", message.content) or re.search(
            r"\bhttps?://\S+", message.content
        ):
            return

        # ボイスチャンネルが未接続の場合はスキップ
        if not self.voice_channel or not message.guild.voice_client:
            print("Bot is not connected to a voice channel. Skipping TTS.")
            return

        if self.voice_channel and message.guild.voice_client:
            try:
                author = str(message.author)
                content = message.content
                timestamp = str(message.created_at)
                print(
                    f"保存するデータ: author={author}, content={content}, timestamp={timestamp}"
                )
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
                tts = gTTS(text=message.content[:200], lang="ja")
                audio_data = io.BytesIO()
                tts.write_to_fp(audio_data)
                audio_data.seek(0)
                await self.audio_queue.put(audio_data)

                if not message.guild.voice_client.is_playing():
                    await self.play_audio(message.guild.voice_client)
            except Exception as e:
                print(f"Error in TTS: {e}")

    async def play_audio(self, voice_client):
        if not voice_client or not voice_client.is_connected():
            print("Error during audio playback: Not connected to voice.")
            return

        while not self.audio_queue.empty():
            if voice_client.is_playing():
                await asyncio.sleep(1)
                continue

            audio_data = await self.audio_queue.get()
            try:
                print("Playing audio...")
                voice_client.play(
                    FFmpegPCMAudio(audio_data, pipe=True),
                    after=lambda e: self.bot.loop.call_soon_threadsafe(
                        self._queue_next
                    ),
                )
            except Exception as e:
                print(f"Error during audio playback: {e}")
                break

    def _queue_next(self):
        """次の音声を再生"""
        if self.voice_channel and self.voice_channel.guild.voice_client:
            if not self.audio_queue.empty():
                self.bot.loop.create_task(
                    self.play_audio(self.voice_channel.guild.voice_client)
                )
            else:
                print("Audio queue is empty. No further playback.")
        else:
            print("Voice channel or voice client is not available.")

    @tasks.loop(seconds=10)
    async def check_voice_channel(self):
        if self.voice_channel:
            voice_client = self.voice_channel.guild.voice_client
            if voice_client and len(self.voice_channel.members) == 1:
                try:
                    await voice_client.disconnect()
                    if voice_client:
                        voice_client.cleanup()
                except Exception as e:
                    print(f"Error during auto-disconnect cleanup: {e}")
                finally:
                    self.voice_channel = None


# CogsにBotを登録
async def setup(bot):
    await bot.add_cog(TTSandDB(bot))
