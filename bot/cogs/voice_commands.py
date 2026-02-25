import logging
import asyncio
import time

from discord.ext import tasks
from discord import VoiceClient

logger = logging.getLogger(__name__)


class VoiceCommands:
    def __init__(self, bot, tts_handler=None):
        logger.info("[VOICE] ボイスコマンドを初期化します")
        self.bot = bot
        self.tts = tts_handler
        self.voice_channel = None
        self._connect_lock = asyncio.Lock()
        self.is_connecting = False
        self.last_active = 0.0
        self.autoleave_grace_seconds = 3
        self.check_voice_channel.start()

    @tasks.loop(seconds=10)
    async def check_voice_channel(self):
        """ボイスチャンネルの自動退出チェック"""
        if not self.voice_channel:
            return

        voice_client = self.voice_channel.guild.voice_client
        if not voice_client:
            return

        non_bot_count = len([m for m in self.voice_channel.members if not m.bot])
        now = time.time()

        if voice_client.is_playing() or non_bot_count > 0:
            self.last_active = now
            return

        if self.is_connecting:
            return

        if self.last_active == 0:
            self.last_active = now
            return

        if now - self.last_active >= self.autoleave_grace_seconds:
            logger.info("[VOICE] 最後のメンバーになったため退出します")
            await self._cleanup_voice(voice_client)

    async def _cleanup_voice(
        self, voice_client: VoiceClient, preserve_queue: bool = False
    ):
        """音声接続のクリーンアップ"""
        try:
            logger.info("[VOICE] 音声接続をクリーンアップします")
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.2)
            if not preserve_queue and self.tts:
                try:
                    self.tts.clear_queue()
                except Exception as e:
                    logger.warning(f"[VOICE] TTSキュークリア中にエラー: {e}")
            await voice_client.disconnect()
            logger.info("[VOICE] ボイスチャンネルから正常に退出しました")
        except Exception as e:
            logger.error(f"[VOICE ERROR] クリーンアップ中にエラーが発生しました: {e}")
        finally:
            self.voice_channel = None
            self.last_active = 0.0

    async def join(self, ctx):
        """ボイスチャンネルに参加"""
        logger.info(f"[VOICE] 参加リクエストを受信: {ctx.author.name}")
        if not ctx.author.voice:
            logger.warning("[VOICE] ユーザーがボイスチャンネルに参加していません")
            return

        target_channel = ctx.author.voice.channel
        logger.info(f"[VOICE] ボイスチャンネルを検出: {target_channel.name}")

        async with self._connect_lock:
            self.is_connecting = True
            try:
                voice_client = ctx.guild.voice_client
                if voice_client:
                    if voice_client.channel != target_channel:
                        logger.info(
                            "[VOICE] 別のボイスチャンネルに接続中のため移動します"
                        )
                        await voice_client.move_to(target_channel)
                        stabilized = await self._wait_for_stable(ctx, target_channel)
                        if not stabilized:
                            logger.warning(
                                "[VOICE] move_to後に安定接続を確認できませんでした。フォールバックを実施します"
                            )
                            try:
                                await self._cleanup_voice(
                                    voice_client, preserve_queue=True
                                )
                            except Exception as e:
                                logger.warning(
                                    f"[VOICE] フォールバック前クリーンアップ中に例外: {e}"
                                )
                            await asyncio.sleep(0.5)
                            await target_channel.connect()
                            stabilized = await self._wait_for_stable(
                                ctx, target_channel
                            )
                            if stabilized:
                                logger.info("[VOICE] フォールバック接続が安定しました")
                            else:
                                logger.error(
                                    "[VOICE ERROR] フォールバック後も安定接続を確認できませんでした"
                                )
                        else:
                            logger.info("[VOICE] 移動が完了し、接続が安定しました")
                    else:
                        logger.info("[VOICE] 既に対象のボイスチャンネルに接続済みです")
                else:
                    logger.info("[VOICE] ボイスチャンネルに接続します")
                    await target_channel.connect()
                    await self._wait_for_stable(ctx, target_channel)

                self.voice_channel = target_channel
                self.last_active = time.time()

                if self.tts:
                    await self.tts.generate_tts("こんにちは")
                    voice_client = ctx.guild.voice_client
                    if voice_client and not voice_client.is_playing():
                        await self.tts.play_audio(voice_client)
            except Exception as e:
                logger.error(
                    f"[VOICE ERROR] 参加/移動処理中にエラーが発生しました: {e}"
                )
            finally:
                self.is_connecting = False

    async def _wait_for_stable(self, ctx, target_channel, timeout: float = 2.0) -> bool:
        """接続が安定するまで待機（最大timeout秒）"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            vc = ctx.guild.voice_client
            if (
                vc
                and getattr(vc, "is_connected", None)
                and vc.is_connected()
                and vc.channel == target_channel
            ):
                return True
            await asyncio.sleep(0.2)
        return False

    async def leave(self, ctx):
        """ボイスチャンネルから退出"""
        logger.info(f"[VOICE] 退出リクエストを受信: {ctx.author.name}")
        if ctx.voice_client:
            await self._cleanup_voice(ctx.voice_client)
