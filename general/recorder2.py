import discord
import os


TOKEN = os.environ.get("TOKEN_MAN")
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = discord.Bot(intents=intents)
connections = {}


@bot.slash_command(description="ボイスチャンネルに参加します。")
async def join(
    ctx,
):
    if ctx.author.voice is None:
        embed = discord.Embed(
            title="エラー",
            description="あなたがボイスチャンネルに参加していません。",
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=embed)
        return
    try:
        await ctx.author.voice.channel.connect()
    except:
        embed = discord.Embed(
            title="エラー",
            description="ボイスチャンネルに接続できません。\nボイスチャンネルの権限を確認してください。",
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=embed)
        return
    embed = discord.Embed(
        title="成功", description="ボイスチャンネルに接続しました。", color=discord.Colour.green()
    )
    await ctx.respond(embed=embed)


@bot.slash_command(description="ボイスチャンネルから切断します。")
async def leave(
    ctx,
):
    if ctx.guild.voice_client is None:
        embed = discord.Embed(
            title="エラー", description="ボイスチャンネルに接続していません。", color=discord.Colour.red()
        )
        await ctx.respond(embed=embed)
        return
    await ctx.guild.voice_client.disconnect()
    embed = discord.Embed(
        title="成功", description="ボイスチャンネルから切断しました。", color=discord.Colour.green()
    )
    await ctx.respond(embed=embed)


@bot.slash_command(description="録音を開始します。")
async def record(ctx):  # If you're using commands.Bot, this will also work.
    voice = ctx.author.voice

    if not voice:
        await ctx.respond("You aren't in a voice channel!")

    # Connect to the voice channel the author is in.
    vc = await voice.channel.connect()
    # Updating the cache with the guild and channel.
    connections.update({ctx.guild.id: vc})

    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel,  # The channel to disconnect from.
    )
    await ctx.respond("Started recording!")


# Our voice client already passes these in.
async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):
    recorded_users = [  # A list of recorded users
        f"<@{user_id}>" for user_id, audio in sink.audio_data.items()
    ]
    await sink.vc.disconnect()  # Disconnect from the voice channel.
    # List down the files.
    files = [
        discord.File(audio.file, f"{user_id}.{sink.encoding}")
        for user_id, audio in sink.audio_data.items()
    ]
    # Send a message with the accumulated files.
    await channel.send(
        f"finished recording audio for: {', '.join(recorded_users)}.", files=files
    )


@bot.slash_command(description="録音を停止します。")
async def stop_recording(ctx):
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        # Stop recording, and call the callback (once_done).
        vc.stop_recording()
        del connections[ctx.guild.id]  # Remove the guild from the cache.
        await ctx.delete()  # And delete.
    else:
        # Respond with this if we aren't recording.
        await ctx.respond("I am currently not recording here.")


bot.run(TOKEN)
