# main_cog.py
from discord.ext import commands
from discord import VoiceClient, FFmpegPCMAudio
import os
from cogs.config import URL_PATTERN, LONG_NUMBER_PATTERN
from cogs.database import db_init, save_message
# from cogs.hayato_api import ask_hayato
from cogs.tts_handler import TTSHandler
from cogs.elevenlabs_tts import ElevenLabsTTS
from cogs.voice_commands import VoiceCommands
import asyncio


class TTSandDB(commands.Cog):
    def __init__(self, bot):
        print("[MAIN] Cogの初期化を開始します")
        self.bot = bot
        self.tts = TTSHandler()
        self.elevenlabs_tts = ElevenLabsTTS()
        self.voice = VoiceCommands(bot, tts_handler=self.tts, elevenlabs_tts=self.elevenlabs_tts)
        self.special_user_id = "514786727634927647"  # 特別なユーザーID
        # 各機能のオン/オフフラグ
        self.hayato_tts_enabled = True  # 音声生成機能
        # self.hayato_reply_enabled = False  # リプライ応答機能 - 基本無効
        # 環境変数のデバッグ出力
        print(
            f"[VOICE_ID DEBUG] ELEVENLABS_VOICE_ID_milk: {os.environ.get('ELEVENLABS_VOICE_ID_milk')}"
        )
        print(
            f"[VOICE_ID DEBUG] ELEVENLABS_VOICE_ID_hayane: {os.environ.get('ELEVENLABS_VOICE_ID_hayane')}"
        )

        self.custom_voice_users = {
            # milk用のボイスID
            "514786727634927647": os.environ.get("ELEVENLABS_VOICE_ID_milk"),
            # hayane用のボイスID
            "1223636376038412338": os.environ.get("ELEVENLABS_VOICE_ID_hayane"),
        }
        db_init()
        print("[MAIN] Cogの初期化が完了しました")

    @commands.command(name="join")
    async def join(self, ctx):
        """ボイスチャンネルに参加するコマンド"""
        print(f"[COMMAND] joinコマンドが実行されました: {ctx.author.name}")
        await self.voice.join(ctx)

    @commands.command(name="leave")
    async def leave(self, ctx):
        """ボイスチャンネルから退出するコマンド"""
        print(f"[COMMAND] leaveコマンドが実行されました: {ctx.author.name}")
        await self.voice.leave(ctx)

    # @commands.command(name="toggle_hayato_reply")
    # async def toggle_hayato_reply(self, ctx):
    #     """hayatoのリプライ応答機能をオン/オフするコマンド"""
    #     # 指定されたユーザーIDのみコマンド実行を許可
    #     if str(ctx.author.id) != self.special_user_id:
    #         print(
    #             f"[COMMAND] 権限がないユーザーがコマンドを実行しようとしました: {ctx.author.name} (ID: {ctx.author.id})"
    #         )
    #         await ctx.send("このコマンドは特定のユーザーのみが実行できます。")
    #         return

    #     self.hayato_reply_enabled = not self.hayato_reply_enabled
    #     status = "有効" if self.hayato_reply_enabled else "無効"
    #     print(f"[COMMAND] hayatoのリプライ応答機能を{status}に切り替えました: {ctx.author.name}")
    #     # await ctx.send(f"hayato reply {status}")

    @commands.command(name="clear_bot")
    async def clear_bot(self, ctx, amount: int = 10):
        """BOTのメッセージを指定した数だけ削除するコマンド """
        # 指定されたユーザーIDのみコマンド実行を許可
        if str(ctx.author.id) != self.special_user_id:
            print(
                f"[COMMAND] 権限がないユーザーがコマンドを実行しようとしました: {ctx.author.name} (ID: {ctx.author.id})"
            )
            await ctx.send("このコマンドは特定のユーザーのみが実行できます。")
            return

        # ユーザーコマンドメッセージの削除は行わない
        print(f"[COMMAND] clear_botコマンドを実行: {ctx.author.name}")

        # amountの値を限定
        if amount <= 0:
            await ctx.send("削除するメッセージ数は1以上を指定してください。", delete_after=5)
            return
        if amount > 100:
            amount = 100  # 一度に削除するメッセージ数を制限

        try:
            # purgeの代わりに手動でBotのメッセージを取得して削除
            deleted_count = 0
            async for message in ctx.channel.history(limit=200):  # 多めに取得
                if deleted_count >= amount:
                    break

                # 自分自身のメッセージのみを削除
                if message.author.id == self.bot.user.id:
                    try:
                        await message.delete()
                        deleted_count += 1
                        # 削除したらちょっと待機（レート制限防止）
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"[COMMAND WARNING] メッセージ削除中にエラー: {e}")

            # 結果を表示
            result_msg = await ctx.send(f"{deleted_count}個のBOTメッセージを削除しました。")
            # 5秒後に通知メッセージも削除するよう試みる
            try:
                await asyncio.sleep(5)
                await result_msg.delete()
            except Exception as e:
                print(f"[COMMAND WARNING] 結果メッセージの削除に失敗しました: {e}")

            print(f"[COMMAND] {ctx.author.name}が{deleted_count}個のBOTメッセージを削除しました")

        except Exception as e:
            await ctx.send(f"メッセージの削除中にエラーが発生しました: {e}")
            print(f"[COMMAND ERROR] メッセージ削除中にエラー: {e}")

    @commands.command(name="play")
    async def play(self, ctx, command_name: str):
        """指定されたコマンドに対応する音声ファイルを再生するコマンド"""
        # 許可されたコマンドとファイルのマッピング
        ALLOWED_FILES = {"とにかくやれ": "とにかくやれ.mp3"}

        # ユーザーがボイスチャンネルに参加しているか確認
        if not ctx.author.voice:
            await ctx.send("ボイスチャンネルに参加してください。")
            return

        # ボイスチャンネルに参加（未接続の場合）
        if not ctx.voice_client:
            await self.join(ctx)

        voice_client = ctx.voice_client

        # コマンドに対応するファイル名を取得
        filename = ALLOWED_FILES.get(command_name)
        if not filename:
            # await ctx.send(f"コマンド '{command_name}' に対応する音声ファイルが見つかりません。")
            return

        # 音声ファイルのパス（カレントディレクトリからの相対パス）
        audio_path = os.path.join("sounds", filename)

        # ファイルの存在確認
        if not os.path.exists(audio_path):
            # await ctx.send(f"ファイル {filename} が見つかりません。")
            return

        # 音声ファイルを再生
        audio_source = FFmpegPCMAudio(audio_path)
        voice_client.play(audio_source)
        # await ctx.send(f"{filename} を再生中...")

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"[MESSAGE] 新しいメッセージを受信: {message.author.name} - {message.content}...")
        # BOT自身のメッセージは処理しない
        if message.author == self.bot.user:
            print(f"[MESSAGE] BOT自身のメッセージをスキップ: {message.content[:30]}...")
            return

        if message.content.startswith("$"):
            print(f"[MESSAGE] コマンドメッセージをスキップ: {message.content}")
            return

        # # メンション処理
        # if self.bot.user in message.mentions:
        #     print(f"[MENTION] メンションを検出: {message.content[:50]}...")
        #     print(
        #         f"[MENTION DEBUG] hayato_reply_enabledフラグの状態: {self.hayato_reply_enabled}"
        #     )

        #     # リプライ応答機能が有効な場合のみ処理
        #     if self.hayato_reply_enabled:
        #         question = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
        #         if question:
        #             print(f"[HAYATO] hayatoに質問を送信します: {question[:30]}...")
        #             try:
        #                 response = ask_hayato(question)
        #                 await message.channel.send(response)

        #                 # hayatoの応答をTTSで再生する処理 - すべてのユーザーが対象
        #                 if (
        #                     self.hayato_tts_enabled
        #                     and self.voice.voice_channel
        #                     and message.guild.voice_client
        #                 ):
        #                     print(
        #                         f"[HAYATO TTS DEBUG] TTSが有効化されています: {self.hayato_tts_enabled}"
        #                     )
        #                     print(
        #                         f"[HAYATO TTS DEBUG] ボイスチャンネル: {self.voice.voice_channel}"
        #                     )
        #                     print(
        #                         f"[HAYATO TTS DEBUG] ギルドボイスクライアント: {message.guild.voice_client}"
        #                     )
        #                     voice_client = message.guild.voice_client
        #                     # milkの音声IDを使用
        #                     # milk_voice_id = os.environ.get("ELEVENLABS_VOICE_ID_milk")
        #                     # if milk_voice_id:
        #                     #     print(
        #                     #         f"[HAYATO TTS] hayatoの応答を音声で再生します: {response[:30]}..."
        #                     #     )
        #                     #     # 現在の再生を停止してから新しい音声を生成する
        #                     #     if voice_client.is_playing():
        #                     #         voice_client.stop()

        #                     #     print(f"[HAYATO TTS DEBUG] 音声生成の前にデバッグ")
        #                     #     print(
        #                     #         f"[HAYATO TTS DEBUG] milk_voice_id: {milk_voice_id}"
        #                     #     )
        #                     #     print(
        #                     #         f"[HAYATO TTS DEBUG] response: {response[:30]}..."
        #                     #     )

        #                     #     # 音声生成（自動キュー追加は無効化）
        #                     #     try:
        #                     #         print(
        #                     #             f"[HAYATO TTS DEBUG] elevenlabs_tts.generate_ttsを呼び出します"
        #                     #         )
        #                     #         file_path = await self.elevenlabs_tts.generate_tts(
        #                     #             response, milk_voice_id, auto_queue=False
        #                     #         )
        #                     #         print(
        #                     #             f"[HAYATO TTS DEBUG] 生成結果のfile_path: {file_path}"
        #                     #         )
        #                     #     except Exception as e:
        #                     #         print(f"[HAYATO TTS ERROR] 音声生成中に例外が発生しました: {e}")
        #                     #     if file_path:
        #                     #         # キューに登録して再生
        #                     #         print(f"[HAYATO TTS] 音声ファイルをキューに追加します: {file_path}")
        #                     #         await self.elevenlabs_tts.audio_queue.put(file_path)
        #                     #         print(
        #                     #             f"[HAYATO TTS] キュー追加完了（現在のサイズ: {self.elevenlabs_tts.audio_queue.qsize()}）"
        #                     #         )
        #                     #         # 再生中でなければ再生を開始
        #                     #         if not voice_client.is_playing():
        #                     #             print(f"[HAYATO TTS] 再生を開始します")
        #                     #             await self.elevenlabs_tts.play_audio(
        #                     #                 voice_client
        #                     #             )
        #                     #     else:
        #                     #         print("[HAYATO TTS ERROR] 音声ファイルの生成に失敗しました")
        #                     # else:
        #                     #     print(
        #                     #         "[HAYATO TTS ERROR] ELEVENLABS_VOICE_ID_milkが設定されていません"
        #                     #     )
                            
        #                     # 一旦通常のTTSを使用
        #                     print(f"[HAYATO TTS] hayatoの応答を音声で再生します: {response[:30]}...")
        #                     if voice_client.is_playing():
        #                         voice_client.stop()
        #                     await self.tts.generate_tts(response)
        #                     if not voice_client.is_playing():
        #                         await self.tts.play_audio(voice_client)
        #             except Exception as e:
        #                 print(f"[HAYATO ERROR] 応答生成時にエラーが発生しました: {e}")
        #                 await message.channel.send("あれ？何かおかしいみたい。もう一度試してみて！")
        #     else:
        #         print(f"[HAYATO] リプライ応答機能が無効化されているため、応答しません")

        # 不適切なメッセージのフィルタリング
        if URL_PATTERN.search(message.content):
            print("[FILTER] URLを含むメッセージをスキップしました")
            return
        if LONG_NUMBER_PATTERN.search(message.content):
            print("[FILTER] 長い数字を含むメッセージをスキップしました")
            return

        # メッセージ保存
        save_message(str(message.author), message.content, str(message.created_at))

        # TTS処理
        if self.voice.voice_channel and message.guild.voice_client:
            voice_client = message.guild.voice_client
            if message.channel == voice_client.channel:
                print("[TTS] ボイスチャット用メッセージを処理します")
                # 特定のユーザーIDの場合はElevenLabsを使用
                # user_id = str(message.author.id)
                # if user_id in self.custom_voice_users:
                #     voice_id = self.custom_voice_users[user_id]
                #     print(
                #         f"[SPECIAL USER] 特別なユーザー {message.author.name} のメッセージを処理します (Voice ID: {voice_id})"
                #     )

                #     # 現在再生中の場合は停止
                #     if voice_client.is_playing():
                #         voice_client.stop()
                #         print("[TTS] 現在の再生を停止しました")

                #     # 音声生成（自動キュー追加は無効化）
                #     file_path = await self.elevenlabs_tts.generate_tts(
                #         message.content, voice_id, auto_queue=False
                #     )
                #     if file_path:
                #         # キューに登録して再生
                #         print(f"[SPECIAL USER] 音声ファイルをキューに追加します: {file_path}")
                #         await self.elevenlabs_tts.audio_queue.put(file_path)
                #         print(
                #             f"[SPECIAL USER] キュー追加完了（現在のサイズ: {self.elevenlabs_tts.audio_queue.qsize()}）"
                #         )
                #         # 再生中でなければ再生を開始
                #         if not voice_client.is_playing():
                #             print(f"[SPECIAL USER] 再生を開始します")
                #             await self.elevenlabs_tts.play_audio(voice_client)
                # else:
                #     # 通常のユーザーは従来のTTSを使用
                #     await self.tts.generate_tts(message.content)
                #     if not voice_client.is_playing():
                #         await self.tts.play_audio(voice_client)
                
                # 一旦全員通常のTTSを使用
                await self.tts.generate_tts(message.content)
                if not voice_client.is_playing():
                    await self.tts.play_audio(voice_client)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        print(
            f"[VOICE STATE] ボイス状態の変更を検出: {member.name} ({before.channel} -> {after.channel})"
        )

        if before.channel == after.channel:
            return

        voice_client = (
            self.voice.voice_channel.guild.voice_client
            if self.voice.voice_channel
            else None
        )
        if not voice_client:
            return

        if after.channel == self.voice.voice_channel:
            text, speed = f"{member.display_name}さんが入室", 1.3
        elif (
            before.channel == self.voice.voice_channel
            and after.channel != self.voice.voice_channel
        ):
            text, speed = f"{member.display_name}さんが退出", 1.3
        else:
            if after.channel is not None:
                text, speed = (
                    f"{after.channel.name}に{member.display_name}さんが入室",
                    1.3,
                )
            else:
                text, speed = (
                    f"{before.channel.name}から{member.display_name}さんが退出",
                    1.3,
                )

        print(f"[VOICE NOTICE] 通知メッセージを生成: {text}")
        await self.tts.generate_tts(text, speed)
        if not voice_client.is_playing():
            await self.tts.play_audio(voice_client)


async def setup(bot):
    print("[MAIN] Cogをセットアップします")
    await bot.add_cog(TTSandDB(bot))
    print("[MAIN] Cogのセットアップが完了しました")
