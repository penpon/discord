# voice_commands.py
from discord.ext import tasks
from discord import VoiceClient

import asyncio
import time


class VoiceCommands:
    def __init__(self, bot, tts_handler=None):
        print("[VOICE] ボイスコマンドを初期化します")
        self.bot = bot
        # TTSハンドラー参照（切断時にキューをクリアするため）
        self.tts = tts_handler
        self.voice_channel = None
        # 接続制御と自動退出の安定化用フラグ
        self._connect_lock = asyncio.Lock()
        self.is_connecting = False
        self.last_active = 0.0
        self.autoleave_grace_seconds = 3  # 単独時に退出するまでの猶予秒
        self.check_voice_channel.start()

    @tasks.loop(seconds=10)
    async def check_voice_channel(self):
        """ボイスチャンネルの自動退出チェック"""
        if not self.voice_channel:
            return

        # print("[VOICE] 自動退出チェックを実行中...")
        voice_client = self.voice_channel.guild.voice_client
        if not voice_client:
            return

        # 非Botメンバー数を算出し、活動タイムスタンプを更新
        non_bot_count = len([m for m in self.voice_channel.members if not m.bot])
        now = time.time()

        if voice_client.is_playing() or non_bot_count > 0:
            self.last_active = now
            return

        # 接続中は退出しない（ハンドシェイク競合を避ける）
        if self.is_connecting:
            return

        # 単独になってから一定時間経過したら退出
        if self.last_active == 0:
            self.last_active = now
            return

        if now - self.last_active >= self.autoleave_grace_seconds:
            print("[VOICE] 最後のメンバーになったため退出します")
            await self._cleanup_voice(voice_client)

    async def _cleanup_voice(
        self, voice_client: VoiceClient, preserve_queue: bool = False
    ):
        """音声接続のクリーンアップ"""
        try:
            print("[VOICE] 音声接続をクリーンアップします")
            if voice_client.is_playing():
                print("[VOICE] 再生中の音声を停止します")
                voice_client.stop()
                # ffmpegのクリーンアップ競合を避けるため、短く待機
                await asyncio.sleep(0.2)
            # 切断時のTTSキュー扱い
            if not preserve_queue:
                try:
                    if self.tts:
                        self.tts.clear_queue()
                    print("[VOICE] TTSキューをクリアしました")
                except Exception as e:
                    print(f"[VOICE WARNING] TTSキュークリア中にエラー: {e}")
            await voice_client.disconnect()
            print("[VOICE] ボイスチャンネルから正常に退出しました")
        except Exception as e:
            print(f"[VOICE ERROR] クリーンアップ中にエラーが発生しました: {str(e)}")
        finally:
            self.voice_channel = None
            self.last_active = 0.0

    async def join(self, ctx):
        """ボイスチャンネルに参加"""
        print(f"[VOICE] 参加リクエストを受信: {ctx.author.name}")
        if not ctx.author.voice:
            print("[VOICE WARN] ユーザーがボイスチャンネルに参加していません")
            return

        target_channel = ctx.author.voice.channel
        print(f"[VOICE] ボイスチャンネルを検出: {target_channel.name}")

        async with self._connect_lock:
            self.is_connecting = True
            try:
                voice_client = ctx.guild.voice_client
                if voice_client:
                    if voice_client.channel != target_channel:
                        print("[VOICE] 別のボイスチャンネルに接続中のため移動します")
                        await voice_client.move_to(target_channel)
                        # 安定待機（0.2s間隔 最大2s）
                        deadline = time.time() + 2.0
                        stabilized = False
                        while time.time() < deadline:
                            vc = ctx.guild.voice_client
                            if (
                                vc
                                and getattr(vc, "is_connected", None)
                                and vc.is_connected()
                                and vc.channel == target_channel
                            ):
                                stabilized = True
                                break
                            await asyncio.sleep(0.2)
                        if not stabilized:
                            print(
                                "[VOICE WARN] move_to後に安定接続を確認できませんでした。フォールバックを実施します"
                            )
                            try:
                                # フォールバック：キュー保持でクリーンアップ→クールダウン→新規接続
                                await self._cleanup_voice(
                                    voice_client, preserve_queue=True
                                )
                            except Exception as e:
                                print(
                                    f"[VOICE WARNING] フォールバック前クリーンアップ中に例外: {e}"
                                )
                            await asyncio.sleep(0.5)  # フォールバック前クールダウン
                            print("[VOICE] フォールバック接続を開始します")
                            await target_channel.connect()
                            # 再度 安定待機（0.2s間隔 最大2s）
                            deadline = time.time() + 2.0
                            stabilized = False
                            while time.time() < deadline:
                                vc = ctx.guild.voice_client
                                if (
                                    vc
                                    and getattr(vc, "is_connected", None)
                                    and vc.is_connected()
                                    and vc.channel == target_channel
                                ):
                                    stabilized = True
                                    break
                                await asyncio.sleep(0.2)
                            if stabilized:
                                print("[VOICE] フォールバック接続が安定しました")
                            else:
                                print(
                                    "[VOICE ERROR] フォールバック後も安定接続を確認できませんでした"
                                )
                        else:
                            print("[VOICE] 移動が完了し、接続が安定しました")
                    else:
                        print("[VOICE] 既に対象のボイスチャンネルに接続済みです")
                else:
                    print("[VOICE] ボイスチャンネルに接続します")
                    await target_channel.connect()
                    # 新規接続時も念のため短い安定待機（0.2s間隔 最大2s）
                    deadline = time.time() + 2.0
                    while time.time() < deadline:
                        vc = ctx.guild.voice_client
                        if (
                            vc
                            and getattr(vc, "is_connected", None)
                            and vc.is_connected()
                            and vc.channel == target_channel
                        ):
                            break
                        await asyncio.sleep(0.2)

                self.voice_channel = target_channel
                self.last_active = time.time()

                # 参加後に「こんにちは」とつぶやく
                if self.tts:
                    await self.tts.generate_tts("こんにちは")
                    voice_client = ctx.guild.voice_client
                    if voice_client and not voice_client.is_playing():
                        await self.tts.play_audio(voice_client)
            except Exception as e:
                print(f"[VOICE ERROR] 参加/移動処理中にエラーが発生しました: {str(e)}")
            finally:
                self.is_connecting = False

    async def leave(self, ctx):
        """ボイスチャンネルから退出"""
        print(f"[VOICE] 退出リクエストを受信: {ctx.author.name}")
        if ctx.voice_client:
            await self._cleanup_voice(ctx.voice_client)
