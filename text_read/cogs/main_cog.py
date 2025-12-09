# main_cog.py
from discord.ext import commands
from discord import VoiceClient, FFmpegPCMAudio
import os
from cogs.config import URL_PATTERN, LONG_NUMBER_PATTERN
from cogs.database import (
    db_init,
    save_message,
    set_user_profile,
    get_user_profile,
    delete_user_profile,
    list_user_profiles,
)

# from cogs.hayato_api import ask_hayato
from cogs.tts_handler import TTSHandler

# from cogs.elevenlabs_tts import ElevenLabsTTS  # ElevenLabs は一時停止中のため無効化
from cogs.voice_commands import VoiceCommands
import asyncio


# TTSプロファイル定義（0=デフォルト、1〜3=ユーザー1〜3）
TTS_PROFILES = {
    0: None,  # デフォルト（フィルタなし）
    1: "equalizer=f=800:t=q:w=1.0:g=0,equalizer=f=4000:t=q:w=1.0:g=3,acompressor=threshold=-18dB:ratio=2:attack=5:release=50,alimiter=limit=0.9,atempo=1.3",  # 明瞭・ニュース調・やや速め
    2: "asetrate=48000*1.059,aresample=48000,atempo=0.60,equalizer=f=3000:t=q:w=1.0:g=3",  # 明るめ・ゆっくり
    3: "asetrate=48000*0.943,aresample=48000,atempo=1.060,equalizer=f=200:t=q:w=1.0:g=2,equalizer=f=3000:t=q:w=1.0:g=-2",  # 低め・標準速度
}


class TTSandDB(commands.Cog):
    def __init__(self, bot):
        print("[MAIN] Cogの初期化を開始します")
        self.bot = bot
        self.tts = TTSHandler()
        self.voice = VoiceCommands(bot, tts_handler=self.tts)  # ElevenLabs を渡さない
        # self.elevenlabs_tts = ElevenLabsTTS()  # ElevenLabs は一時停止
        self.special_user_id = "514786727634927647"  # 特別なユーザーID
        # 各機能のオン/オフフラグ
        # self.hayato_tts_enabled = True  # 音声生成機能
        # self.hayato_reply_enabled = False  # リプライ応答機能 - 基本無効
        # 環境変数のデバッグ出力
        # print(f"[VOICE_ID DEBUG] ELEVENLABS_VOICE_ID_milk: {os.environ.get('ELEVENLABS_VOICE_ID_milk')}")
        # print(f"[VOICE_ID DEBUG] ELEVENLABS_VOICE_ID_hayane: {os.environ.get('ELEVENLABS_VOICE_ID_hayane')}")

        # self.custom_voice_users = {
        #     # milk用のボイスID
        #     "514786727634927647": os.environ.get("ELEVENLABS_VOICE_ID_milk"),
        #     # hayane用のボイスID
        #     "1223636376038412338": os.environ.get("ELEVENLABS_VOICE_ID_hayane"),
        # }
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

    @commands.command(name="tts_profile_set")
    async def tts_profile_set(self, ctx, user: commands.MemberConverter, profile: int):
        """ユーザーにTTSプロファイルを割り当て（特定ユーザー限定）"""
        # 特定ユーザーIDのみコマンド実行を許可
        if str(ctx.author.id) != self.special_user_id:
            print(f"[COMMAND] 権限がないユーザーがコマンドを実行しようとしました: {ctx.author.name} (ID: {ctx.author.id})")
            await ctx.send("このコマンドは特定のユーザーのみが実行できます。")
            return
        
        print(f"[COMMAND] tts_profile_setコマンドを実行: {ctx.author.name} -> {user.name} = {profile}")
        
        # プロファイル番号の検証
        if profile not in TTS_PROFILES:
            await ctx.send(f"❌ プロファイル番号は0〜3の範囲で指定してください。")
            return
        
        # DBに保存
        set_user_profile(str(user.id), profile)
        
        profile_names = ["デフォルト", "ユーザー1（明瞭・ニュース調）", "ユーザー2（明るめ・速め）", "ユーザー3（低め・標準速度）"]
        await ctx.send(f"✅ {user.mention} のTTSプロファイルを **{profile_names[profile]}** に設定しました。")
    
    @commands.command(name="tts_profile_clear")
    async def tts_profile_clear(self, ctx, user: commands.MemberConverter):
        """ユーザーのTTSプロファイル割当を削除（特定ユーザー限定）"""
        # 特定ユーザーIDのみコマンド実行を許可
        if str(ctx.author.id) != self.special_user_id:
            print(f"[COMMAND] 権限がないユーザーがコマンドを実行しようとしました: {ctx.author.name} (ID: {ctx.author.id})")
            await ctx.send("このコマンドは特定のユーザーのみが実行できます。")
            return
        
        print(f"[COMMAND] tts_profile_clearコマンドを実行: {ctx.author.name} -> {user.name}")
        
        delete_user_profile(str(user.id))
        await ctx.send(f"✅ {user.mention} のTTSプロファイル割当を削除しました（デフォルトに戻ります）。")
    
    @commands.command(name="tts_profile_show")
    async def tts_profile_show(self, ctx, user: commands.MemberConverter = None):
        """ユーザーの現在のTTSプロファイルを表示"""
        target_user = user or ctx.author
        print(f"[COMMAND] tts_profile_showコマンドを実行: {ctx.author.name} -> {target_user.name}")
        
        profile = get_user_profile(str(target_user.id))
        if profile is None:
            profile = 0  # 未登録はデフォルト扱い
        if profile not in TTS_PROFILES:
            profile = 0
        
        profile_names = ["デフォルト", "ユーザー1（明瞭・ニュース調）", "ユーザー2（明るめ・やや高め）", "ユーザー3（低め・落ち着き）"]
        await ctx.send(f"🔊 {target_user.mention} のTTSプロファイル: **{profile_names[profile]}** (ID: {profile})")
    
    @commands.command(name="tts_profile_list")
    async def tts_profile_list(self, ctx):
        """全ユーザーのTTSプロファイル割当一覧を表示（特定ユーザー限定）"""
        # 特定ユーザーIDのみコマンド実行を許可
        if str(ctx.author.id) != self.special_user_id:
            print(f"[COMMAND] 権限がないユーザーがコマンドを実行しようとしました: {ctx.author.name} (ID: {ctx.author.id})")
            await ctx.send("このコマンドは特定のユーザーのみが実行できます。")
            return
        
        print(f"[COMMAND] tts_profile_listコマンドを実行: {ctx.author.name}")
        
        profiles = list_user_profiles()
        
        if not profiles:
            await ctx.send("📋 現在、プロファイルが割り当てられているユーザーはいません。")
            return
        
        profile_names = ["デフォルト", "ユーザー1", "ユーザー2", "ユーザー3"]
        
        # ユーザー名を取得して表示
        lines = ["📋 **TTSプロファイル割当一覧**"]
        for user_id, profile_id in profiles:
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_name = user.name
            except:
                user_name = f"Unknown (ID: {user_id})"
            
            display_id = profile_id if profile_id in TTS_PROFILES else 0
            lines.append(f"・{user_name}: {profile_names[display_id]} (ID: {display_id})")
        
        await ctx.send("\n".join(lines))

    @commands.command(name="play")
    async def play(self, ctx, command_name: str):
        """指定されたコマンドに対応する音声ファイルを再生するコマンド"""
        # 許可されたコマンドとファイルのマッピング
         # ALLOWED_FILES = {"とにかくやれ": "とにかくやれ.mp3", "ぬの歌": "ぬの歌.mp3", "はやねの歌": "はやねの歌.mp3", "なつきの歌": "なつきの歌.mp3", "めむむの歌": "めむむの歌.mp3"}
        ALLOWED_FILES = {"ぬの歌": "ぬの歌.mp3", "はやねの歌": "はやねの歌.mp3", "なつきの歌": "なつきの歌.mp3", "めむむの歌": "めむむの歌.mp3"}

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

        def after_playing(error):
            if error:
                print(f"[VOICE ERROR] 再生エラー: {error}")
            
            # 再生終了後のクリーンアップ処理（スレッド削除など）
            # スレッドIDが保存されているか確認する必要があるため、インスタンス変数または
            # create_taskで非同期処理をスケジュールする
            coro = self._cleanup_lyrics_thread(ctx)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"[VOICE ERROR] クリーンアップタスクのスケジュールに失敗: {e}")

        voice_client.play(audio_source, after=after_playing)
        
        # 歌詞ファイルの確認とスレッド作成
        txt_filename = filename.rsplit('.', 1)[0] + '.txt'
        txt_path = os.path.join("sounds", txt_filename)
        
        if os.path.exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    lyrics_content = f.read()
                
                # スレッド作成元のメッセージを送信
                now_playing_msg = await ctx.send(f"🎵 **{command_name}** を再生中...")
                
                # スレッドを作成 (auto_archive_duration=60 は1時間だが、手動でアーカイブ/削除予定)
                thread = await now_playing_msg.create_thread(
                    name=f"Lyrics: {command_name}",
                    auto_archive_duration=60
                )
                
                # 歌詞を投稿 (2000文字制限を考慮して分割投稿が必要かもしれないが、一旦そのまま)
                # 長すぎる場合は分割するロジックを入れるのが安全
                if len(lyrics_content) > 1900:
                    for i in range(0, len(lyrics_content), 1900):
                        await thread.send(lyrics_content[i:i+1900])
                else:
                    await thread.send(lyrics_content)
                
                # クリーンアップ用にスレッド情報を保存 (簡易的な実装としてctxに紐付けるか、辞書で管理)
                # ctxオブジェクト自体は永続しない可能性があるため、辞書管理が望ましいが
                # ここでは簡易的にクラス変数で管理する
                if not hasattr(self, 'active_lyrics_threads'):
                    self.active_lyrics_threads = {}
                
                self.active_lyrics_threads[ctx.guild.id] = thread

            except Exception as e:
                print(f"[VOICE ERROR] 歌詞スレッドの作成に失敗: {e}")
                await ctx.send(f"⚠️ 歌詞の読み込みに失敗しました: {e}")
        else:
            await ctx.send(f"🎵 **{command_name}** を再生中... (歌詞ファイルなし)")

    async def _cleanup_lyrics_thread(self, ctx):
        """再生終了後に呼ばれるクリーンアップ処理"""
        print(f"[VOICE] 再生終了クリーンアップを開始: {ctx.guild.name}")
        if hasattr(self, 'active_lyrics_threads') and ctx.guild.id in self.active_lyrics_threads:
            thread = self.active_lyrics_threads.pop(ctx.guild.id)
            if thread:
                try:
                    # スレッドをアーカイブ or 削除
                    # print(f"[VOICE] 歌詞スレッドをロック/アーカイブします: {thread.name}")
                    # await thread.edit(archived=True, locked=True) 
                    
                    # 要件は「自動削除」のようなものだったので、削除してしまう
                    print(f"[VOICE] 歌詞スレッドを削除します: {thread.name}")
                    await thread.delete()
                    
                    # 親メッセージも削除するかは要件次第だが、とりあえずスレッドだけで十分か
                    # 親メッセージの削除も試みる
                    try:
                        channel = thread.parent
                        if channel:
                            parent_msg = await channel.fetch_message(thread.id) # スレッドID = 親メッセージID
                            await parent_msg.delete()
                    except:
                        pass # 親メッセージが見つからない等は無視

                except Exception as e:
                    print(f"[VOICE ERROR] スレッド削除中にエラー: {e}")

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
                
                # ユーザーのTTSプロファイルを取得
                user_id = str(message.author.id)
                profile_id = get_user_profile(user_id)
                if profile_id is None:
                    profile_id = 0  # 未登録はデフォルト
                if profile_id not in TTS_PROFILES:
                    profile_id = 0
                
                # プロファイルからフィルタを取得
                ffmpeg_filter = TTS_PROFILES.get(profile_id)
                print(f"[TTS] ユーザー {message.author.name} のプロファイル: {profile_id}, フィルタ: {ffmpeg_filter}")
                
                # TTS生成とキュー追加（プロファイルフィルタを適用）
                playback_speed = 1.75 if profile_id == 1 else 1.0
                await self.tts.generate_tts(message.content, speed=playback_speed, ffmpeg_filter=ffmpeg_filter)
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
        # 未接続状態ではTTS生成・再生を行わない
        if (
            not getattr(voice_client, "is_connected", None)
            or not voice_client.is_connected()
        ):
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
