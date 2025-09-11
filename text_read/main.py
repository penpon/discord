import discord
from discord.ext import commands
import cogs.main_cog as main_cog
import cogs.general as general
import os

# TOKEN = os.environ.get("TOKEN_MAN")
TOKEN = os.environ.get("TOKEN_NU")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
# intents = discord.Intents.all()
# client = discord.Client(intents=intents)

client = commands.Bot(command_prefix="$", intents=intents)


@client.event
async def on_ready():
    print("-----")
    print(client.user.name)
    print(client.user.id)
    print(discord.__version__)
    print("-----")
    try:
        await main_cog.setup(client)
        await general.setup(client)
        # プレイ中の状態を設定する
        # await client.change_presence(activity=discord.Game(name="ポケモンクイズ"))
        await client.change_presence(
            activity=discord.CustomActivity(name="👾読み上げBot稼働中👾")
        )
    except discord.errors.ClientException as e:
        print(e)


@client.event
async def on_disconnect():
    print("Connection lost. Attempting to reconnect...")
    # await client.close()
    # await client.login(TOKEN)
    # await client.connect()


client.run(TOKEN)
