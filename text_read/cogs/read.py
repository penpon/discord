from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from gtts import gTTS
import os
import re
import datetime
import glob

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.check_voice_channel.start()  # タスクループを開始

    def delete_files_with_prefix(self):
        directory = '.'  # カレントディレクトリ
        prefix = 'output_'  # プレフィックス
        # ディレクトリ内の指定したプレフィックスを持つファイルを検索
        for file in glob.glob(os.path.join(directory, f'{prefix}*')):
            os.remove(file)
            print(f"Deleted: {file}")

    @commands.command(name='join')
    async def join(self, ctx):
        """ボイスチャンネルに参加します"""
        self.voice_channel = ctx.author.voice.channel
        if self.voice_channel and not ctx.voice_client:
            await self.voice_channel.connect()

    @commands.command(name='leave')
    async def leave(self, ctx):
        """ボイスチャンネルから切断します"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.delete_files_with_prefix()
            self.voice_channel = None  # ボイスチャンネルの参照をリセット

    @commands.Cog.listener()
    async def on_message(self, message):
        # ボット自身のメッセージには反応しない
        if message.author == self.bot.user:
            return

        # 数字が5桁以上のメッセージを無視
        if re.search(r'\b\d{5,}\b', message.content) or re.search(r'\bhttps?://\S+', message.content):
            return

        # ボットが接続しているボイスチャンネルに対してのみメッセージを読み上げる
        if self.voice_channel and message.channel.id == self.voice_channel.id:
            try:
                tts = gTTS(text=message.content, lang='ja')
                filename = f"output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                tts.save(filename)

                if message.guild.voice_client and message.guild.voice_client.is_connected():
                    message.guild.voice_client.play(FFmpegPCMAudio(filename))
            except Exception as e: 
                print("-----------------------")
                print(e)
                print("-----------------------")

    @tasks.loop(seconds=10)  # 10秒ごとにチェック
    async def check_voice_channel(self):
        if self.voice_channel:
            voice_client = self.voice_channel.guild.voice_client
            if voice_client and len(self.voice_channel.members) == 1:
                # チャンネルが空になった場合に切断
                await voice_client.disconnect()
                self.delete_files_with_prefix()
                self.voice_channel = None  # ボイスチャンネルの参照をリセット

# CogsにBotを登録
async def setup(bot):
    await bot.add_cog(TTS(bot))
