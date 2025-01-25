# main_cog.py

from discord.ext import commands
from discord import VoiceClient
from cogs.config import URL_PATTERN, LONG_NUMBER_PATTERN
from cogs.database import db_init, save_message
from cogs.deepseek import ask_deepseek
from cogs.tts_handler import TTSHandler
from cogs.voice_commands import VoiceCommands
import asyncio


class TTSandDB(commands.Cog):
    def __init__(self, bot):
        print("[MAIN] Cogの初期化を開始します")
        self.bot = bot
        self.tts = TTSHandler()
        self.voice = VoiceCommands(bot)
        db_init()
        print("[MAIN] Cogの初期化が完了しました")

    @commands.command(name="join")
    async def join(self, ctx):
        """ボイスチャンネルに参加するコマンド"""
        print(f"[COMMAND] joinコマンドが実行されました: {ctx.author.name}")
        await self.voice.join(ctx)

    @commands.command(name="leave")
    async def leave(self, ctx):
        """ボイスチャンネルから退出するコマンド"""
        print(f"[COMMAND] leaveコマンドが実行されました: {ctx.author.name}")
        await self.voice.leave(ctx)
        self.tts.clear_queue()

    @commands.Cog.listener()
    async def on_message(self, message):
        # if message.author == self.bot.user:
        #     return

        print(f"[MESSAGE] 新しいメッセージを受信: {message.author.name} - {message.content}...")

        if message.content.startswith("$"):
            print(f"[MESSAGE] コマンドメッセージをスキップ: {message.content}")
            return

        # メンション処理
        if self.bot.user in message.mentions:
            print(f"[MENTION] メンションを検出: {message.content[:50]}...")
            question = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if question:
                response = ask_deepseek(question)
                await message.channel.send(response)

        # 不適切なメッセージのフィルタリング
        if URL_PATTERN.search(message.content):
            print("[FILTER] URLを含むメッセージをスキップしました")
            return
        if LONG_NUMBER_PATTERN.search(message.content):
            print("[FILTER] 長い数字を含むメッセージをスキップしました")
            return

        # メッセージ保存
        save_message(str(message.author), message.content, str(message.created_at))

        # TTS処理
        if self.voice.voice_channel and message.guild.voice_client:
            voice_client = message.guild.voice_client
            if message.channel == voice_client.channel:
                print("[TTS] ボイスチャット用メッセージを処理します")
                await self.tts.generate_tts(message.content)
                if not voice_client.is_playing():
                    await self.tts.play_audio(voice_client)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        print(
            f"[VOICE STATE] ボイス状態の変更を検出: {member.name} ({before.channel} -> {after.channel})"
        )
        voice_client = (
            self.voice.voice_channel.guild.voice_client
            if self.voice.voice_channel
            else None
        )
        # botがどこにも参加していない場合は通知しない
        if not voice_client:
            return

        # 入退室通知文言を生成する関数
        def generate_notification_text():
            if after.channel == self.voice.voice_channel:
                return f"{member.display_name}さんが入室しました", 1.2
            elif before.channel == self.voice.voice_channel:
                return f"{member.display_name}さんが退出しました", 1.2
            if after.channel is not None:
                return f"{after.channel.name}部屋に{member.display_name}さんが入室しました", 1.2
            if before.channel is not None:
                return (
                    f"{before.channel.name}部屋から{member.display_name}さんが退出しました",
                    1.2,
                )
            return None, None

        text, speed = generate_notification_text()
        if text:
            print(f"[VOICE NOTICE] 通知メッセージを生成: {text}")
            await self.tts.generate_tts(text, speed)
            if not voice_client.is_playing():
                await self.tts.play_audio(voice_client)


async def setup(bot):
    print("[MAIN] Cogをセットアップします")
    await bot.add_cog(TTSandDB(bot))
    print("[MAIN] Cogのセットアップが完了しました")
