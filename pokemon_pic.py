import discord
import csv
from googletrans import Translator
import os


TOKEN = os.environ.get("TOKEN_MAN")
# TOKEN = os.environ.get("TOKEN_NU")


# 接続に必要なオブジェクトを生成
intents = discord.Intents.default()
intents.message_content = True
#  intents = discord.Intents.all()
client = discord.Client(intents=intents)

def csv_to_dict(csv_file):
    data_dict = {}
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        # ヘッダ行を読み込み、辞書のキーとして使用
        headers = next(csv_reader)
        for row in csv_reader:
            # 辞書のキーはポケモン名、値は番号とする
            data_dict[row[0]] = int(row[1])
    return data_dict

# CSVファイルを辞書型に変換
pokemon_dict = csv_to_dict('/Users/nana/PycharmProjects/sample_MAN/pokemon_fix.csv')

# 起動時に動作する処理
@client.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(f"client user name: {client.user.name}")
    print(f"client user id: {client.user.id}")
    print('------')

@client.event
async def on_disconnect():
    print('Bot has been disconnected.')

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
    # sampleMAN
    # if message.content.startswith("<@1231884500842319903>"):
    #     content = message.content.removeprefix("<@1231884500842319903>").strip()
    # ぬ
    if message.content.startswith("<@1231577595330428979>"):
        content = message.content.removeprefix("<@1231577595330428979>").strip()
        if content in pokemon_dict:
            file_path = f"/Users/nana/PycharmProjects/sample_MAN/pokemon_jpg/{pokemon_dict[content]}.jpg"
            await message.reply(file=discord.File(file_path))

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
