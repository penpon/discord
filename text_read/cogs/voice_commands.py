# voice_commands.py
from discord.ext import tasks
from discord import VoiceClient


class VoiceCommands:
    def __init__(self, bot):
        print("[VOICE] ボイスコマンドを初期化します")
        self.bot = bot
        self.voice_channel = None
        self.check_voice_channel.start()

    @tasks.loop(seconds=10)
    async def check_voice_channel(self):
        """ボイスチャンネルの自動退出チェック"""
        if self.voice_channel:
            # print("[VOICE] 自動退出チェックを実行中...")
            voice_client = self.voice_channel.guild.voice_client
            if voice_client and len(self.voice_channel.members) == 1:
                print("[VOICE] 最後のメンバーになったため退出します")
                await self._cleanup_voice(voice_client)

    async def _cleanup_voice(self, voice_client: VoiceClient):
        """音声接続のクリーンアップ"""
        try:
            print("[VOICE] 音声接続をクリーンアップします")
            if voice_client.is_playing():
                print("[VOICE] 再生中の音声を停止します")
                voice_client.stop()
            await voice_client.disconnect()
            print("[VOICE] ボイスチャンネルから正常に退出しました")
        except Exception as e:
            print(f"[VOICE ERROR] クリーンアップ中にエラーが発生しました: {str(e)}")
        finally:
            self.voice_channel = None

    async def join(self, ctx):
        """ボイスチャンネルに参加"""
        print(f"[VOICE] 参加リクエストを受信: {ctx.author.name}")
        if ctx.author.voice:
            print(f"[VOICE] ボイスチャンネルを検出: {ctx.author.voice.channel.name}")
            self.voice_channel = ctx.author.voice.channel
            if not ctx.voice_client:
                print("[VOICE] ボイスチャンネルに接続します")
                await self.voice_channel.connect()
        else:
            print("[VOICE WARN] ユーザーがボイスチャンネルに参加していません")

    async def leave(self, ctx):
        """ボイスチャンネルから退出"""
        print(f"[VOICE] 退出リクエストを受信: {ctx.author.name}")
        if ctx.voice_client:
            await self._cleanup_voice(ctx.voice_client)
