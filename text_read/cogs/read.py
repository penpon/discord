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
        # audio_queue には (audio_data, speed) のタプルを入れる
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
                # 音声再生を停止し、キューをクリア
                ctx.voice_client.stop()
                while not self.audio_queue.empty():
                    await self.audio_queue.get()
                # ボイスクライアントの切断
                await ctx.voice_client.disconnect()
            except Exception as e:
                print(f"Error during disconnect: {e}")
            finally:
                self.voice_channel = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.startswith("$"):
            print(f"Ignoring message starting with $: {message.content}")
            return

        # 数字のみの長文やURLをスキップする
        if re.search(r"\b\d{5,}\b", message.content) or re.search(
            r"\bhttps?://\S+", message.content
        ):
            return

        author = str(message.author)
        content = message.content
        timestamp = str(message.created_at)
        print(
            f"保存するデータ: author={author}, content={content}, channel={message.channel}, timestamp={timestamp}"
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

        # Botがボイスチャンネルにいない場合はスキップ
        if not self.voice_channel or not message.guild.voice_client:
            print("Bot is not connected to a voice channel. Skipping TTS.")
            return

        voice_client = message.guild.voice_client
        # メッセージがBotのいるチャンネルじゃなければスキップ
        if message.channel != voice_client.channel:
            print("Message is not from the bot's voice channel. Ignoring message.")
            return

        try:
            tts = gTTS(text=message.content, lang="ja")
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            audio_data.seek(0)
            # メッセージ読み上げなので speed=1.0 (等倍)
            await self.audio_queue.put((audio_data, 1.0))

            if not message.guild.voice_client.is_playing():
                await self.play_audio(message.guild.voice_client)
        except Exception as e:
            print(f"Error in TTS: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """ユーザがボイスチャンネルに入室/退出したときに名前を読み上げる"""
        if member.bot:
            return  # Botは無視

        # Botが現在接続しているチャンネル（self.voice_channel）を取得
        bot_channel = self.voice_channel
        voice_client = bot_channel.guild.voice_client if bot_channel else None

        # --- 「botがいるボイスチャンネル」にユーザが入室した(入室時だけ2倍速) ---
        if after.channel == bot_channel and before.channel != after.channel:
            if voice_client and voice_client.is_connected():
                try:
                    # 入室時は速度を2倍
                    tts_text = f"{member.display_name}さんが入室しました"
                    tts = gTTS(text=tts_text, lang="ja")
                    audio_data = io.BytesIO()
                    tts.write_to_fp(audio_data)
                    audio_data.seek(0)
                    await self.audio_queue.put((audio_data, 1.2))  # ★2倍速

                    if not voice_client.is_playing():
                        await self.play_audio(voice_client)
                except Exception as e:
                    print(f"Error in TTS for voice join: {e}")

        # 「botがいるボイスチャンネル」からユーザが退出した(退出は等倍)
        elif before.channel == bot_channel and after.channel != bot_channel:
            if voice_client and voice_client.is_connected():
                try:
                    # 退出時は通常速度
                    tts_text = f"{member.display_name}さんが退出しました"
                    tts = gTTS(text=tts_text, lang="ja")
                    audio_data = io.BytesIO()
                    tts.write_to_fp(audio_data)
                    audio_data.seek(0)
                    await self.audio_queue.put((audio_data, 1.2))

                    if not voice_client.is_playing():
                        await self.play_audio(voice_client)
                except Exception as e:
                    print(f"Error in TTS for voice leave: {e}")

        # --- Botがいない他の部屋に入室した(入室は2倍速) ---
        elif (
            after.channel
            and after.channel != bot_channel
            and before.channel != after.channel
        ):
            if voice_client and voice_client.is_connected():
                try:
                    tts_text = f"{after.channel.name} に、{member.display_name}さんが入室しました"
                    tts = gTTS(text=tts_text, lang="ja")
                    audio_data = io.BytesIO()
                    tts.write_to_fp(audio_data)
                    audio_data.seek(0)
                    await self.audio_queue.put((audio_data, 1.2))  # ★2倍速

                    if not voice_client.is_playing():
                        await self.play_audio(voice_client)
                except Exception as e:
                    print(f"Error in TTS for voice join in another channel: {e}")

        # --- Botがいない他の部屋から退出した(退出は等倍) ---
        elif (
            before.channel
            and before.channel != bot_channel
            and after.channel != before.channel
        ):
            if voice_client and voice_client.is_connected():
                try:
                    tts_text = (
                        f"{before.channel.name} から、{member.display_name}さんが退出しました"
                    )
                    tts = gTTS(text=tts_text, lang="ja")
                    audio_data = io.BytesIO()
                    tts.write_to_fp(audio_data)
                    audio_data.seek(0)
                    await self.audio_queue.put((audio_data, 1.2))

                    if not voice_client.is_playing():
                        await self.play_audio(voice_client)
                except Exception as e:
                    print(f"Error in TTS for voice leave in another channel: {e}")

    async def play_audio(self, voice_client):
        if not voice_client or not voice_client.is_connected():
            print("Error during audio playback: Not connected to voice.")
            return

        while not self.audio_queue.empty():
            if voice_client.is_playing():
                await asyncio.sleep(1)
                continue

            # キューから (audio_data, speed) を取り出す
            audio_data, speed = await self.audio_queue.get()
            try:
                print(f"Playing audio... speed={speed}")
                # 再生速度を調整: -af atempo={speed}
                voice_client.play(
                    FFmpegPCMAudio(
                        audio_data, pipe=True, options=f"-af atempo={speed}"
                    ),
                    after=lambda e: self.bot.loop.call_soon_threadsafe(
                        self._queue_next
                    ),
                )
            except Exception as e:
                print(f"Error during audio playback: {e}")
                break

    def _queue_next(self):
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
            # ボイスチャンネル内がBot1人(=メンバー数1)の場合は自動で抜ける
            if voice_client and len(self.voice_channel.members) == 1:
                try:
                    await voice_client.disconnect()
                    print("Successfully disconnected from the voice channel.")

                    if voice_client:
                        voice_client.cleanup()
                        print("Voice client cleanup completed.")

                except Exception as e:
                    print(f"Error during auto-disconnect cleanup: {e}")
                finally:
                    self.voice_channel = None


async def setup(bot):
    await bot.add_cog(TTSandDB(bot))
