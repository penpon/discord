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

        # デバッグ情報を追加
        print(f"[ELEVENLABS DEBUG] APIキーの存在: {self.api_key is not None}")
        if self.api_key:
            print(f"[ELEVENLABS DEBUG] APIキーの長さ: {len(self.api_key)}")
        print(f"[ELEVENLABS DEBUG] ボイスIDの存在: {self.voice_id is not None}")
        if self.voice_id:
            print(f"[ELEVENLABS DEBUG] ボイスIDの長さ: {len(self.voice_id)}")

        if not self.api_key or not self.voice_id:
            print("[ELEVENLABS ERROR] APIキーまたはボイスIDが設定されていません")

        self.audio_queue = asyncio.Queue()
        self.output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sounds"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_tts(self, text: str, voice_id=None):
        """ElevenLabs APIを使用してTTS音声を生成"""
        # パラメータが指定されていない場合はデフォルトのボイスIDを使用
        current_voice_id = voice_id if voice_id else self.voice_id
        print(f"[ELEVENLABS] 音声生成を開始: {text[:20]}... (Voice ID: {current_voice_id})")

        if not self.api_key or not current_voice_id:
            print("[ELEVENLABS ERROR] APIキーまたはボイスIDが設定されていません")
            return

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

            # APIにリクエストを送信
            response = requests.post(
                f"{self.URL}/{current_voice_id}", json=data, headers=headers
            )

            if response.status_code != 200:
                print(
                    f"[ELEVENLABS ERROR] APIエラー: {response.status_code} - {response.text}"
                )
                return

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

            # キューに追加
            await self.audio_queue.put(file_path)
            print(f"[ELEVENLABS] キューに追加しました（現在のキューサイズ: {self.audio_queue.qsize()}）")

        except Exception as e:
            print(f"[ELEVENLABS ERROR] 音声生成に失敗しました: {str(e)}")

    async def play_audio(self, voice_client):
        """音声再生のメイン処理"""
        print("[ELEVENLABS] 音声再生処理を開始します")
        while not self.audio_queue.empty():
            if voice_client.is_playing():
                print("[ELEVENLABS] 現在再生中のため待機します...")
                await asyncio.sleep(0.5)
                continue

            file_path = await self.audio_queue.get()
            try:
                print(f"[ELEVENLABS] 再生を開始します: {file_path}")
                voice_client.play(
                    FFmpegPCMAudio(file_path),
                    after=lambda e: self._queue_next(voice_client, file_path),
                )
            except Exception as e:
                print(f"[ELEVENLABS ERROR] 再生中にエラーが発生しました: {str(e)}")

    def _queue_next(self, voice_client, file_path):
        """次の音声を再生するためのコールバック"""
        print("[ELEVENLABS] 次の音声をチェックします")
        # 古いファイルを削除（オプション）
        # try:
        #     os.remove(file_path)
        #     print(f"[ELEVENLABS] ファイルを削除しました: {file_path}")
        # except Exception as e:
        #     print(f"[ELEVENLABS ERROR] ファイル削除に失敗しました: {str(e)}")

        if not self.audio_queue.empty():
            print("[ELEVENLABS] 次の音声を再生開始します")
            asyncio.run_coroutine_threadsafe(
                self.play_audio(voice_client), voice_client.loop
            )

    def clear_queue(self):
        """キューをクリア"""
        print("[ELEVENLABS] キューをクリアします")
        self.audio_queue = asyncio.Queue()
