import discord
import os
from discord.ext import commands
import asyncio

TOKEN = os.environ.get("TOKEN_MAN")
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

connections = {}


@bot.command(name="join", description="ボイスチャンネルに参加し、録音を開始します。")
async def join(ctx):
    if ctx.author.voice is None:
        embed = discord.Embed(
            title="エラー",
            description="あなたがボイスチャンネルに参加していません。",
            color=discord.Colour.red(),
        )
        await ctx.send(embed=embed)
        return
    try:
        vc = await ctx.author.voice.channel.connect()
        connections[ctx.guild.id] = vc
        # 自動的に録音を開始する
        await start_recording(ctx)
    except:
        embed = discord.Embed(
            title="エラー",
            description="ボイスチャンネルに接続できません。\nボイスチャンネルの権限を確認してください。",
            color=discord.Colour.red(),
        )
        await ctx.send(embed=embed)
        return
    embed = discord.Embed(
        title="成功", description="ボイスチャンネルに接続し、録音を開始しました。", color=discord.Colour.green()
    )
    await ctx.send(embed=embed)


@bot.command(name="leave", description="ボイスチャンネルから切断し、録音を停止します。")
async def leave(ctx):
    if ctx.guild.voice_client is None:
        embed = discord.Embed(
            title="エラー", description="ボイスチャンネルに接続していません。", color=discord.Colour.red()
        )
        await ctx.send(embed=embed)
        return

    # 録音を停止
    if ctx.guild.id in connections:
        vc = connections[ctx.guild.id]
        vc.stop_recording()  # 録音を停止
        del connections[ctx.guild.id]  # 接続情報を削除

    await ctx.guild.voice_client.disconnect()
    embed = discord.Embed(
        title="成功", description="ボイスチャンネルから切断し、録音を停止しました。", color=discord.Colour.green()
    )
    await ctx.send(embed=embed)


@bot.command(name="record", description="録音を開始します。")
async def record(ctx):
    voice = ctx.author.voice
    if not voice:
        await ctx.send("You aren't in a voice channel!")

    # Connect to the voice channel the author is in.
    vc = await voice.channel.connect()
    # Updating the cache with the guild and channel.
    connections.update({ctx.guild.id: vc})

    await start_recording(ctx)
    await ctx.send("Started recording!")


async def start_recording(ctx):
    vc = connections[ctx.guild.id]

    # Start recording using the MP3Sink.
    vc.start_recording(
        discord.sinks.MP3Sink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel,  # The channel to send the recording result.
    )


async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):
    recorded_users = [  # A list of recorded users
        f"<@{user_id}>" for user_id, audio in sink.audio_data.items()
    ]

    # Save the audio files to local storage
    saved_files = []
    for user_id, audio in sink.audio_data.items():
        file_path = f"/Users/nana/workspace/discord/general/{user_id}.mp3"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(audio.file.read())
        saved_files.append(discord.File(file_path, filename=f"{user_id}.mp3"))

    await sink.vc.disconnect()  # Disconnect from the voice channel.

    # Send a message with the accumulated files.
    await channel.send(
        f"Finished recording audio for: {', '.join(recorded_users)}.", files=saved_files
    )


@bot.command(name="stop_recording", description="録音を停止します。")
async def stop_recording(ctx):
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        # Stop recording, and call the callback (once_done).
        vc.stop_recording()
        del connections[ctx.guild.id]  # Remove the guild from the cache.
        await ctx.send("Recording stopped!")
    else:
        # Respond with this if we aren't recording.
        await ctx.send("I am currently not recording here.")


bot.run(TOKEN)
