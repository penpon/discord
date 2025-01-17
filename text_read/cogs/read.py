from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from gtts import gTTS
import re
import io
from asyncio import Queue


class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.audio_queue = Queue()
        self.check_voice_channel.start()

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
            await ctx.voice_client.disconnect()
            self.voice_channel = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if re.search(r"\b\d{5,}\b", message.content) or re.search(
            r"\bhttps?://\S+", message.content
        ):
            return

        if self.voice_channel and message.channel.id == self.voice_channel.id:
            try:
                tts = gTTS(text=message.content[:200], lang="ja")
                audio_data = io.BytesIO()
                tts.write_to_fp(audio_data)
                audio_data.seek(0)  # バッファの先頭に戻す
                await self.audio_queue.put(audio_data)

                if not message.guild.voice_client.is_playing():
                    await self.play_audio(message.guild.voice_client)
            except Exception as e:
                print(f"Error in TTS: {e}")

    async def play_audio(self, voice_client):
        while not self.audio_queue.empty():
            audio_data = await self.audio_queue.get()
            voice_client.play(
                FFmpegPCMAudio(audio_data, pipe=True),
                after=lambda _: self.bot.loop.call_soon_threadsafe(self._queue_next),
            )

    def _queue_next(self):
        if not self.audio_queue.empty():
            self.bot.loop.create_task(
                self.play_audio(self.voice_channel.guild.voice_client)
            )

    @tasks.loop(seconds=10)
    async def check_voice_channel(self):
        if self.voice_channel:
            voice_client = self.voice_channel.guild.voice_client
            if voice_client and len(self.voice_channel.members) == 1:
                await voice_client.disconnect()
                self.voice_channel = None


# CogsにBotを登録
async def setup(bot):
    await bot.add_cog(TTS(bot))
