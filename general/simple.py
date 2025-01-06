import discord
import os


TOKEN = os.environ.get("TOKEN_MAN")
# TOKEN = os.environ.get("TOKEN_NU")

# 接続に必要なオブジェクトを生成
# intents = discord.Intents.default()
# intents.message_content = True
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# 起動時に動作する処理
@client.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(f"client user name: {client.user.name}")
    print(f"client user id: {client.user.id}")
    print('------')

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    if message.content.startswith("<@1231884500842319903>"):
        # メンションを削除
        content = message.content.removeprefix("<@1231884500842319903>")
        # 空白を削除して内容を取得
        content = content.strip()
        if content == 'ping':
            await message.channel.send('pong!')
        elif content == 'ぬ':
            await message.channel.send('ぬ')
        else:
            await message.channel.send(content)

# before: このメソッドが呼ばれる状態の前
# 音声ルームに入室前: なにもない
# 音声ルームに退室後: 色々ある
@client.event
async def on_voice_state_update(member, before, after):
    if after.channel:
        print(f"{member}が入室しました")
        # target_user_name = "pipeline.hayane"
        # target_user = discord.utils.get(member.guild.members, name=target_user_name)

        channel_id = '1231884045579980875'
        user_id = '514786727634927647'
        # user_id = '1223636376038412338'

        channel = client.get_channel(int(channel_id))
        user = client.get_user(int(user_id))

        print(user)

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
