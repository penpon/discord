import sys
import os
import logging

# プロジェクトルートおよびbot/ディレクトリをPYTHONPATHに追加（どこから起動しても動くよう設定）
_bot_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_bot_dir)
if _bot_dir not in sys.path:
    sys.path.insert(0, _bot_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import discord
from discord.ext import commands
from cogs import main_cog
from cogs import general

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN_NU")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = commands.Bot(command_prefix="$", intents=intents)


@client.event
async def setup_hook():
    """Cog読み込み（起動時に一度だけ実行）"""
    await main_cog.setup(client)
    await general.setup(client)
    logger.info("全てのCogを読み込みました")


@client.event
async def on_ready():
    logger.info("-----")
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info(discord.__version__)
    logger.info("-----")
    await client.change_presence(
        activity=discord.CustomActivity(name="👾読み上げBot稼働中👾")
    )


@client.event
async def on_disconnect():
    logger.warning("Connection lost. Attempting to reconnect...")


if not TOKEN:
    logger.critical("TOKEN_NU is not set. Exiting.")
    sys.exit(1)

client.run(TOKEN)
