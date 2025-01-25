import discord
import os
from discord.ext import commands
import asyncio

TOKEN = os.environ.get("TOKEN_MAN")
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

# ギルドIDをキーにしてVoiceClientを保持する辞書
connections = {}


@bot.command(name="join", description="ボイスチャンネルに参加します。")
async def join(ctx):
    print(f"[DEBUG] joinコマンドが呼び出されました。発行者: {ctx.author}, サーバー: {ctx.guild}")

    # ユーザがボイスチャンネルにいない場合はエラー
    if ctx.author.voice is None:
        print("[ERROR] あなたがボイスチャンネルに参加していません。")
        return

    channel = ctx.author.voice.channel
    print(f"[DEBUG] ボイスチャンネル『{channel}』に接続を試みます。")
    try:
        vc = await channel.connect()
        connections[ctx.guild.id] = vc
        print(f"[DEBUG] ボイスチャンネル『{channel}』への接続に成功しました。")
    except Exception as e:
        print(f"[ERROR] ボイスチャンネルに接続できませんでした: {e}")
        return

    print("[INFO] ボイスチャンネルに接続しました。録音はまだ開始していません。")


@bot.command(name="leave", description="ボイスチャンネルから切断し、録音を停止します。")
async def leave(ctx):
    print(f"[DEBUG] leaveコマンドが呼び出されました。発行者: {ctx.author}, サーバー: {ctx.guild}")

    # ボイスチャンネルに接続していない場合はエラー
    if ctx.guild.id not in connections:
        print("[ERROR] ボイスチャンネルに接続していません。")
        return

    vc = connections[ctx.guild.id]

    # 録音を試しに停止（録音中でなければ例外が発生する可能性あり）
    try:
        vc.stop_recording()
        print("[DEBUG] leaveコマンド内で録音を停止しました。")
    except Exception as e:
        print(f"[DEBUG] leaveコマンド内で録音停止を試みましたが、録音中ではない可能性があります: {e}")

    # ボイスチャンネルから切断
    await vc.disconnect()
    del connections[ctx.guild.id]
    print("[INFO] ボイスチャンネルから切断しました。")


@bot.command(name="start", description="録音を開始します。")
async def start(ctx):
    print(f"[DEBUG] startコマンドが呼び出されました。発行者: {ctx.author}, サーバー: {ctx.guild}")

    # 接続しているかどうか確認
    if ctx.guild.id not in connections:
        print("[ERROR] まだボイスチャンネルに接続していません。先にjoinコマンドを使用してください。")
        return

    vc = connections[ctx.guild.id]
    if not vc.is_connected():
        print("[ERROR] ボイスチャンネルに接続していません。")
        return

    # 録音を開始
    try:
        print("[DEBUG] 録音を開始します。")
        vc.start_recording(
            discord.sinks.MP3Sink(),  # 音声をMP3形式で録音
            once_done,  # 録音終了後に呼ばれるコールバック
            ctx.channel,  # （録音終了後の結果を送信するチャンネル。実際に送信はしないが引数で渡す）
        )
        print("[INFO] 録音を開始しました。")
    except Exception as e:
        print(f"[ERROR] 録音を開始できませんでした: {e}")


@bot.command(name="stop", description="録音を停止します。")
async def stop(ctx):
    print(f"[DEBUG] stopコマンドが呼び出されました。発行者: {ctx.author}, サーバー: {ctx.guild}")

    # 接続していない or キャッシュに存在しない場合はエラー
    if ctx.guild.id not in connections:
        print("[ERROR] ボイスチャンネルに接続していません。先にjoinコマンドを使用してください。")
        return

    vc = connections[ctx.guild.id]
    # 録音停止を試みる
    try:
        vc.stop_recording()
        print("[INFO] 録音を停止しました。")
    except Exception as e:
        print(f"[ERROR] 録音を停止できませんでした: {e}")


async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):
    print("[DEBUG] once_doneコールバックが呼び出されました。録音データをファイルに書き込みます。")

    # 録音されたユーザー一覧（デバッグ用）
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
    print(f"[DEBUG] 録音対象ユーザー: {', '.join(recorded_users)}")

    # 音声ファイルの保存
    for user_id, audio in sink.audio_data.items():
        file_path = f"./recorded/{user_id}.mp3"  # 実行環境に合わせてパスを変更してください
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(audio.file.read())

    # ここでボイスチャンネルから切断しないことに注意（leaveコマンドに任せる）
    print("[INFO] once_doneコールバック処理が完了しました。録音ファイルの書き込みが終了しました。")


bot.run(TOKEN)
