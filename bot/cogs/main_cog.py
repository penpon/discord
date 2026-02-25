import logging
import os
import asyncio

from discord.ext import commands
from discord import FFmpegPCMAudio

from core.config import URL_PATTERN, LONG_NUMBER_PATTERN, SOUNDS_DIR, ADMIN_USER_ID
from core.database import (
    db_init,
    save_message,
    set_user_profile,
    get_user_profile,
    delete_user_profile,
    list_user_profiles,
)
from core.tts_handler import TTSHandler
from cogs.voice_commands import VoiceCommands

logger = logging.getLogger(__name__)

# TTSプロファイル定義（0=デフォルト、1〜3=ユーザー1〜3）
TTS_PROFILES = {
    0: None,  # デフォルト（フィルタなし）
    1: "equalizer=f=800:t=q:w=1.0:g=0,equalizer=f=4000:t=q:w=1.0:g=3,acompressor=threshold=-18dB:ratio=2:attack=5:release=50,alimiter=limit=0.9,atempo=1.3",
    2: "asetrate=48000*1.059,aresample=48000,atempo=0.60,equalizer=f=3000:t=q:w=1.0:g=3",
    3: "asetrate=48000*0.943,aresample=48000,atempo=1.060,equalizer=f=200:t=q:w=1.0:g=2,equalizer=f=3000:t=q:w=1.0:g=-2",
}

PROFILE_NAMES = {
    0: "デフォルト",
    1: "ユーザー1（明瞭・ニュース調）",
    2: "ユーザー2（明るめ・速め）",
    3: "ユーザー3（低め・標準速度）",
}

# ファイル再生コマンドのマッピング
ALLOWED_FILES = {
    "pipeline": "pipeline.mp3",
    "ぬ": "ぬの歌.mp3",
    "はやね": "はやねの歌.mp3",
    "なつき": "なつきの歌.mp3",
    "めむむ": "めむむの歌.mp3",
}


class TTSandDB(commands.Cog):
    def __init__(self, bot):
        logger.info("[MAIN] Cogの初期化を開始します")
        self.bot = bot
        self.tts = TTSHandler()
        self.voice = VoiceCommands(bot, tts_handler=self.tts)
        self.active_lyrics_messages: dict = {}
        db_init()
        logger.info("[MAIN] Cogの初期化が完了しました")

    def _is_admin(self, ctx) -> bool:
        """管理者ユーザーかチェック"""
        return str(ctx.author.id) == ADMIN_USER_ID

    async def _deny_non_admin(self, ctx) -> bool:
        """管理者以外のユーザーをブロックし、Trueを返す（通過の場合はFalse）"""
        if not self._is_admin(ctx):
            logger.warning(
                f"[COMMAND] 権限のないユーザーがコマンドを実行: {ctx.author.name} (ID: {ctx.author.id})"
            )
            await ctx.send("このコマンドは特定のユーザーのみが実行できます。")
            return True
        return False

    @commands.command(name="join")
    async def join(self, ctx):
        """ボイスチャンネルに参加するコマンド"""
        logger.info(f"[COMMAND] join: {ctx.author.name}")
        await self.voice.join(ctx)

    @commands.command(name="leave")
    async def leave(self, ctx):
        """ボイスチャンネルから退出するコマンド"""
        logger.info(f"[COMMAND] leave: {ctx.author.name}")
        await self.voice.leave(ctx)

    @commands.command(name="clear_bot")
    async def clear_bot(self, ctx, amount: int = 10):
        """BOTのメッセージを指定した数だけ削除するコマンド"""
        if await self._deny_non_admin(ctx):
            return

        logger.info(f"[COMMAND] clear_bot: {ctx.author.name}, amount={amount}")

        if amount <= 0:
            await ctx.send(
                "削除するメッセージ数は1以上を指定してください。", delete_after=5
            )
            return
        if amount > 100:
            amount = 100

        try:
            deleted_count = 0
            async for message in ctx.channel.history(limit=200):
                if deleted_count >= amount:
                    break
                if message.author.id == self.bot.user.id:
                    try:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"[COMMAND] メッセージ削除中にエラー: {e}")

            result_msg = await ctx.send(
                f"{deleted_count}個のBOTメッセージを削除しました。"
            )
            try:
                await asyncio.sleep(5)
                await result_msg.delete()
            except Exception as e:
                logger.warning(f"[COMMAND] 結果メッセージの削除に失敗: {e}")

            logger.info(
                f"[COMMAND] {ctx.author.name}が{deleted_count}個のBOTメッセージを削除しました"
            )

        except Exception as e:
            await ctx.send(f"メッセージの削除中にエラーが発生しました: {e}")
            logger.error(f"[COMMAND ERROR] メッセージ削除中にエラー: {e}")

    @commands.command(name="tts_profile_set")
    async def tts_profile_set(self, ctx, user: commands.MemberConverter, profile: int):
        """ユーザーにTTSプロファイルを割り当て（特定ユーザー限定）"""
        if await self._deny_non_admin(ctx):
            return

        logger.info(
            f"[COMMAND] tts_profile_set: {ctx.author.name} -> {user.name} = {profile}"
        )

        if profile not in TTS_PROFILES:
            await ctx.send(
                f"❌ プロファイル番号は0〜{max(TTS_PROFILES.keys())}の範囲で指定してください。"
            )
            return

        set_user_profile(str(user.id), profile)
        await ctx.send(
            f"✅ {user.mention} のTTSプロファイルを **{PROFILE_NAMES[profile]}** に設定しました。"
        )

    @commands.command(name="tts_profile_clear")
    async def tts_profile_clear(self, ctx, user: commands.MemberConverter):
        """ユーザーのTTSプロファイル割当を削除（特定ユーザー限定）"""
        if await self._deny_non_admin(ctx):
            return

        logger.info(f"[COMMAND] tts_profile_clear: {ctx.author.name} -> {user.name}")
        delete_user_profile(str(user.id))
        await ctx.send(
            f"✅ {user.mention} のTTSプロファイル割当を削除しました（デフォルトに戻ります）。"
        )

    @commands.command(name="tts_profile_show")
    async def tts_profile_show(self, ctx, user: commands.MemberConverter = None):
        """ユーザーの現在のTTSプロファイルを表示"""
        target_user = user or ctx.author
        logger.info(
            f"[COMMAND] tts_profile_show: {ctx.author.name} -> {target_user.name}"
        )

        profile = get_user_profile(str(target_user.id)) or 0
        if profile not in TTS_PROFILES:
            profile = 0

        await ctx.send(
            f"🔊 {target_user.mention} のTTSプロファイル: **{PROFILE_NAMES[profile]}** (ID: {profile})"
        )

    @commands.command(name="tts_profile_list")
    async def tts_profile_list(self, ctx):
        """全ユーザーのTTSプロファイル割当一覧を表示（特定ユーザー限定）"""
        if await self._deny_non_admin(ctx):
            return

        logger.info(f"[COMMAND] tts_profile_list: {ctx.author.name}")
        profiles = list_user_profiles()

        if not profiles:
            await ctx.send(
                "📋 現在、プロファイルが割り当てられているユーザーはいません。"
            )
            return

        lines = ["📋 **TTSプロファイル割当一覧**"]
        for user_id, profile_id in profiles:
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_name = user.name
            except Exception:
                user_name = f"Unknown (ID: {user_id})"

            display_id = profile_id if profile_id in TTS_PROFILES else 0
            lines.append(
                f"・{user_name}: {PROFILE_NAMES[display_id]} (ID: {display_id})"
            )

        await ctx.send("\n".join(lines))

    @commands.command(name="play")
    async def play(self, ctx, command_name: str):
        """指定されたコマンドに対応する音声ファイルを再生するコマンド"""
        if not ctx.author.voice:
            await ctx.send("ボイスチャンネルに参加してください。")
            return

        if not ctx.voice_client:
            await self.join(ctx)

        voice_client = ctx.voice_client
        filename = ALLOWED_FILES.get(command_name)
        if not filename:
            return

        audio_path = os.path.join(SOUNDS_DIR, filename)
        if not os.path.exists(audio_path):
            logger.warning(f"[PLAY] ファイルが見つかりません: {audio_path}")
            return

        audio_source = FFmpegPCMAudio(audio_path)

        def after_playing(error):
            if error:
                logger.error(f"[VOICE ERROR] 再生エラー: {error}")
            coro = self._cleanup_lyrics_messages(ctx)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                logger.error(
                    f"[VOICE ERROR] クリーンアップタスクのスケジュールに失敗: {e}"
                )

        voice_client.play(audio_source, after=after_playing)

        txt_filename = filename.rsplit(".", 1)[0] + ".txt"
        txt_path = os.path.join(SOUNDS_DIR, txt_filename)
        lyrics_messages = []

        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    lyrics_content = f.read()
                now_playing_msg = await ctx.send(f"🎵 **{command_name}** を再生中...")
                lyrics_messages.append(now_playing_msg)
                if len(lyrics_content) > 1900:
                    for i in range(0, len(lyrics_content), 1900):
                        msg = await ctx.send(lyrics_content[i : i + 1900])
                        lyrics_messages.append(msg)
                else:
                    msg = await ctx.send(lyrics_content)
                    lyrics_messages.append(msg)
                self.active_lyrics_messages[ctx.guild.id] = lyrics_messages
            except Exception as e:
                logger.error(f"[VOICE ERROR] 歌詞の読み込みに失敗: {e}")
                await ctx.send(f"⚠️ 歌詞の読み込みに失敗しました: {e}")
        else:
            now_playing_msg = await ctx.send(
                f"🎵 **{command_name}** を再生中... (歌詞ファイルなし)"
            )
            lyrics_messages.append(now_playing_msg)
            self.active_lyrics_messages[ctx.guild.id] = lyrics_messages

    async def _cleanup_lyrics_messages(self, ctx):
        """再生終了後に呼ばれるクリーンアップ処理（歌詞メッセージ削除）"""
        logger.info(f"[VOICE] 再生終了クリーンアップ: {ctx.guild.name}")
        if ctx.guild.id in self.active_lyrics_messages:
            messages = self.active_lyrics_messages.pop(ctx.guild.id)
            for msg in messages:
                try:
                    await msg.delete()
                except Exception as e:
                    logger.warning(f"[VOICE] メッセージ削除中にエラー: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        logger.debug(
            f"[MESSAGE] 受信: {message.author.name} - {message.content[:30]}..."
        )
        if message.author == self.bot.user:
            return
        if message.content.startswith("$"):
            return
        if URL_PATTERN.search(message.content):
            logger.debug("[FILTER] URLを含むメッセージをスキップ")
            return
        if LONG_NUMBER_PATTERN.search(message.content):
            logger.debug("[FILTER] 長い数字を含むメッセージをスキップ")
            return

        save_message(str(message.author), message.content, str(message.created_at))

        if self.voice.voice_channel and message.guild.voice_client:
            voice_client = message.guild.voice_client
            if message.channel == voice_client.channel:
                user_id = str(message.author.id)
                profile_id = get_user_profile(user_id) or 0
                if profile_id not in TTS_PROFILES:
                    profile_id = 0

                ffmpeg_filter = TTS_PROFILES.get(profile_id)
                playback_speed = 1.75 if profile_id == 1 else 1.0
                logger.info(f"[TTS] {message.author.name}: profile={profile_id}")
                await self.tts.generate_tts(
                    message.content, speed=playback_speed, ffmpeg_filter=ffmpeg_filter
                )
                if not voice_client.is_playing():
                    await self.tts.play_audio(voice_client)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if before.channel == after.channel:
            return

        voice_client = (
            self.voice.voice_channel.guild.voice_client
            if self.voice.voice_channel
            else None
        )
        if not voice_client:
            return
        if (
            not getattr(voice_client, "is_connected", None)
            or not voice_client.is_connected()
        ):
            return

        if after.channel == self.voice.voice_channel:
            text, speed = f"{member.display_name}さんが入室", 1.3
        elif (
            before.channel == self.voice.voice_channel
            and after.channel != self.voice.voice_channel
        ):
            text, speed = f"{member.display_name}さんが退出", 1.3
        else:
            if after.channel is not None:
                text, speed = (
                    f"{after.channel.name}に{member.display_name}さんが入室",
                    1.3,
                )
            else:
                text, speed = (
                    f"{before.channel.name}から{member.display_name}さんが退出",
                    1.3,
                )

        logger.info(f"[VOICE NOTICE] {text}")
        await self.tts.generate_tts(text, speed)
        if not voice_client.is_playing():
            await self.tts.play_audio(voice_client)


async def setup(bot):
    logger.info("[MAIN] Cogをセットアップします")
    await bot.add_cog(TTSandDB(bot))
    logger.info("[MAIN] Cogのセットアップが完了しました")
