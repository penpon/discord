import logging
from discord.ext import commands

logger = logging.getLogger(__name__)


class General(commands.Cog, name="一般"):
    """一般的なユーティリティコマンド"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Botの応答状態を確認します"""
        logger.info("pong!")
        await ctx.send("pong!")


async def setup(bot):
    await bot.add_cog(General(bot))
