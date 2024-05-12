import discord
from discord.ext import commands
import cogs.quiz as quiz
import cogs.general as general
import os

# TOKEN = os.environ.get("TOKEN_MAN")
TOKEN = os.environ.get("TOKEN_NU")

intents = discord.Intents.default()
intents.message_content = True
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
        await quiz.setup(client)
        await general.setup(client)
    except discord.errors.ClientException as e:
        print(e)

@client.event
async def on_disconnect():
    print("Connection lost. Attempting to reconnect...")
    # await client.close()
    # await client.login(TOKEN)
    # await client.connect()

@bot.command()
async def help(ctx, arg=None):
    if arg == "ping":
        await ctx.send("Ping Command:\n  $ping - Checks the bot's latency.")
    if arg == "quiz":
        await ctx.send("Quiz Command:\n  The quiz command conducts a quiz.")

client.run(TOKEN)
