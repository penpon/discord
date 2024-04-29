import discord
import random
import requests
import os

wordlist = ["それ禁止"]

TOKEN = os.environ.get("TOKEN_MAN")
# TOKEN = os.environ.get("TOKEN_NU")

# 接続に必要なオブジェクトを生成
intents = discord.Intents.default()
intents.message_content = True
#  intents = discord.Intents.all()
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
    if message.content == 'ping':
        await message.channel.send('pong!')
    if message.content == 'ぬ':
        await message.channel.send('ぬ')
    if "犬" in message.content:
        # APIから画像を取得
        response = requests.get('https://dog.ceo/api/breeds/image/random')
        data = response.json()
        image_url = data['message']
        await message.reply(image_url)
    if "猫" in message.content:
        # APIから画像を取得
        response = requests.get('https://api.thecatapi.com/v1/images/search?api_key=live_YqSencQiiYxURU1BMuY970WZiVBT71OenTnShR9vwNQcHOcYX70po8d35SiH4RAC')
        data = response.json()
        image_url = data[0]['url']
        await message.reply(image_url)
    if "狐" in message.content:
        # APIから画像を取得
        response = requests.get('https://randomfox.ca/floof/')
        data = response.json()
        image_url = data['image']
        await message.reply(image_url)
    if "https://tenor.com" in message.content:
        random_word = random.choice(wordlist)
        await message.reply(random_word)
    if message.content.startswith("<@1231884500842319903>"):
        # メンションを削除
        content = message.content.removeprefix("<@1231884500842319903>").strip()
        await message.reply(content)



# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
