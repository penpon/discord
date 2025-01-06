from discord.ext import commands
import discord
import csv
import random
import asyncio
import os

home_dir = os.path.expanduser("~")

class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    def csv_to_dict(self, csv_file):
        data_dict = {}
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            # ヘッダ行を読み込み、辞書のキーとして使用
            headers = next(csv_reader)
            for row in csv_reader:
                # 辞書のキーはポケモン名、値は番号とする
                data_dict[row[0]] = int(row[1])
        return data_dict

    @commands.command()
    async def quiz(self, ctx):
        '''
        Starts a quiz
        '''
        await ctx.send("ポケモンクイズを始めます！")
        random_number = random.randint(1, 721)
        try:
            file_path = f"{home_dir}/pokemon_jpg/{random_number}.jpg"
            await ctx.send(file=discord.File(file_path))
        except Exception as e:
            print(e)

        def check(message):
            # return message.author == ctx.author and message.channel == ctx.channel
            return message.channel == ctx.channel

        pokemon_dict = self.csv_to_dict(f"/{home_dir}/pokemon_fix.csv")

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=30)
            if pokemon_dict[reply.content] == random_number:
                await ctx.send("正解です！")
        except asyncio.TimeoutError:
            name = next(key for key, value in pokemon_dict.items() if value == random_number)
            await ctx.send("時間切れです。")
            await ctx.send(f"正解は{name}です！")
            print(f"Time out")
            print(f"Answer: {name}")
        except KeyError as e:
            name = next(key for key, value in pokemon_dict.items() if value == random_number)
            await ctx.send("不正解です！")
            await ctx.send(f"正解は{name}です！")
            print(f"User Input: {e}")
            print(f"Answer: {name}")



async def setup(bot):
    await bot.add_cog(Quiz(bot))
