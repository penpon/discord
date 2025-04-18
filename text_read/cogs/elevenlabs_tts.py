# elevenlabs_tts.py
import os
import time
import requests
import asyncio
import io
from discord import FFmpegPCMAudio


class ElevenLabsTTS:
    URL = "https://api.elevenlabs.io/v1/text-to-speech"

    def __init__(self):
        print("[ELEVENLABS] ElevenLabs TTSハンドラーを初期化します")
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

        # デバッグ情報は非表示に変更
        # デバッグが必要な場合はここのコメントを外してください
        # print(f"[ELEVENLABS DEBUG] APIキーの存在: {self.api_key is not None}")
        # if self.api_key:
        #     print(f"[ELEVENLABS DEBUG] APIキーの長さ: {len(self.api_key)}")
        # print(f"[ELEVENLABS DEBUG] ボイスIDの存在: {self.voice_id is not None}")
        # if self.voice_id:
        #     print(f"[ELEVENLABS DEBUG] ボイスIDの長さ: {len(self.voice_id)}")

        # エラーメッセージも非表示にします
        # if not self.api_key or not self.voice_id:
        #     print("[ELEVENLABS ERROR] APIキーまたはボイスIDが設定されていません")

        self.audio_queue = asyncio.Queue()
        self.output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sounds"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_tts(self, text: str, voice_id=None, auto_queue=True):
        """ElevenLabs APIを使用してTTS音声を生成"""
        # パラメータが指定されていない場合はデフォルトのボイスIDを使用
        current_voice_id = voice_id if voice_id else self.voice_id
        print(f"[ELEVENLABS] 音声生成を開始: {text[:20]}... (Voice ID: {current_voice_id})")

        if not self.api_key or not current_voice_id:
            # エラーメッセージを非表示にしました
            # print("[ELEVENLABS ERROR] APIキーまたはボイスIDが設定されていません")
            return None

        try:
            # APIリクエストのヘッダーとデータを設定
            headers = {
                "Accept": "audio/wav",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            }

            data = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "speed": 0.85,
                    "stability": 0.8,
                    "similarity_boost": 0.8,
                },
                "output_format": "wav",
            }

            # デバッグ情報
            print(f"[ELEVENLABS DEBUG] APIキーの長さ: {len(self.api_key) if self.api_key else 'None'}")
            print(f"[ELEVENLABS DEBUG] リクエストURL: {self.URL}/{current_voice_id}")
            print(f"[ELEVENLABS DEBUG] データ: {data}")
            
            # APIにリクエストを送信
            print(f"[ELEVENLABS DEBUG] APIリクエストを送信します")
            response = requests.post(
                f"{self.URL}/{current_voice_id}", json=data, headers=headers
            )
            print(f"[ELEVENLABS DEBUG] APIレスポンスステータス: {response.status_code}")

            if response.status_code != 200:
                print(
                    f"[ELEVENLABS ERROR] APIエラー: {response.status_code} - {response.text}"
                )
                return None

            # レスポンスデータをバイナリストリームに変換
            audio_data = io.BytesIO(response.content)
            audio_data.seek(0)

            # ファイル名を生成
            filename = f"elevenlabs_{int(time.time())}.wav"
            file_path = os.path.join(self.output_dir, filename)

            # 音声データをファイルに書き込む
            with open(file_path, "wb") as audio_file:
                audio_file.write(response.content)

            print(f"[ELEVENLABS] 音声ファイルを保存しました: {file_path}")

            # auto_queueパラメータがTrueの場合のみキューに追加
            if auto_queue:
                await self.audio_queue.put(file_path)
                print(f"[ELEVENLABS] キューに自動追加しました（現在のキューサイズ: {self.audio_queue.qsize()}）")
            
            # 生成したファイルパスを返す
            return file_path

        except Exception as e:
            print(f"[ELEVENLABS ERROR] 音声生成に失敗しました: {str(e)}")
            return None

    async def play_audio(self, voice_client):
        """音声再生のメイン処理"""
        print("[ELEVENLABS] 音声再生処理を開始します")
        
        # 既に再生中なら何もせず終了
        if voice_client.is_playing():
            print("[ELEVENLABS] 現在再生中です。次の音声は自動的にキューから再生されます")
            return
            
        # キューが空でなければ処理開始
        if not self.audio_queue.empty():
            try:
                # ファイルパスを取得
                file_path = await self.audio_queue.get()
                print(f"[ELEVENLABS] 再生を開始します: {file_path}")
                
                # FFmpegPCMAudioの作成とエラーチェック
                try:
                    audio_source = FFmpegPCMAudio(file_path)
                    print(f"[ELEVENLABS] 音声ソース作成に成功しました")
                except Exception as e:
                    print(f"[ELEVENLABS ERROR] 音声ソース作成に失敗しました: {e}")
                    # エラーが発生したら次のキューを処理するタスクを作成
                    asyncio.create_task(self._play_next_audio(voice_client, file_path, None))
                    return
                    
                # 再生処理とコールバック設定
                voice_client.play(
                    audio_source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self._play_next_audio(voice_client, file_path, e), voice_client.loop
                    )
                )
                print(f"[ELEVENLABS] 再生が正常に開始されました: {file_path}")
                
            except Exception as e:
                print(f"[ELEVENLABS ERROR] 再生処理中に予期せぬエラーが発生しました: {str(e)}")
                # エラーが発生しても次の処理を開始
                asyncio.create_task(self._play_next_audio(voice_client, "error", None))
        else:
            print("[ELEVENLABS] キューが空のため再生を終了します")

    async def _play_next_audio(self, voice_client, file_path, error):
        """次の音声を再生するための非同期コールバック"""
        if error:
            print(f"[ELEVENLABS ERROR] 再生エラー: {error}")

        print(f"[ELEVENLABS] 音声再生完了: {file_path}")
        
        # キューが空でなければ次の音声を再生
        if not self.audio_queue.empty():
            print("[ELEVENLABS] 次の音声を再生します...")
            # 少し待機してから次の音声再生を開始
            await asyncio.sleep(0.1)
            await self.play_audio(voice_client)
        else:
            print("[ELEVENLABS] キューが空になりました。再生を終了します")

    def clear_queue(self):
        """キューをクリア"""
        print("[ELEVENLABS] キューをクリアします")
        self.audio_queue = asyncio.Queue()
