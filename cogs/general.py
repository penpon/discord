from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.command()
    # async def exit(self, ctx):
    #     print("終了します")
    #     await ctx.send("終了します！")
    #     await self.bot.close()

    @commands.command()
    async def ping(self, ctx):
        '''
        Checks the bot's status.
        '''
        print("pong!")
        await ctx.send("pong!")

async def setup(bot):
    await bot.add_cog(General(bot))
