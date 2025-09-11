# tts_handler.py
from gtts import gTTS
import io
from discord import FFmpegPCMAudio
import asyncio


class TTSHandler:
    def __init__(self):
        print("[TTS] TTSハンドラーを初期化します")
        self.audio_queue = asyncio.Queue()

    def _synthesize_tts(self, text: str) -> io.BytesIO:
        """同期処理: gTTSで音声を生成（スレッドにオフロードして呼び出す）"""
        tts = gTTS(text=text, lang="ja")
        audio_data = io.BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)
        return audio_data

    async def generate_tts(self, text: str, speed: float = 1.0):
        """TTS音声の生成とキュー追加"""
        print(f"[TTS] 音声生成を開始: {text[:20]}... (速度: {speed}x)")
        try:
            # gTTSは同期I/Oのためイベントループをブロックしないようスレッドにオフロード
            audio_data = await asyncio.to_thread(self._synthesize_tts, text)
            await self.audio_queue.put((audio_data, speed))
            print(f"[TTS] キューに追加しました（現在のキューサイズ: {self.audio_queue.qsize()}）")
        except Exception as e:
            print(f"[TTS ERROR] 音声生成に失敗しました: {str(e)}")

    async def play_audio(self, voice_client):
        """音声再生のメイン処理"""
        print("[TTS] 音声再生処理を開始します")
        # 接続確認
        if not getattr(voice_client, "is_connected", None) or not voice_client.is_connected():
            print("[TTS] VoiceClientが未接続のため再生を中止します")
            return
        while not self.audio_queue.empty():
            if voice_client.is_playing():
                print("[TTS] 現在再生中のため待機します...")
                await asyncio.sleep(0.5)
                continue

            audio_data, speed = await self.audio_queue.get()
            try:
                print(f"[TTS] 再生を開始します（速度: {speed}x）")
                voice_client.play(
                    FFmpegPCMAudio(
                        audio_data, pipe=True, options=f"-af atempo={speed}"
                    ),
                    after=lambda e: self._queue_next(voice_client),
                )
            except Exception as e:
                print(f"[TTS ERROR] 再生中にエラーが発生しました: {str(e)}")

    def _queue_next(self, voice_client):
        """次の音声を再生するためのコールバック"""
        print("[TTS] 次の音声をチェックします")
        # 接続確認
        if not getattr(voice_client, "is_connected", None) or not voice_client.is_connected():
            print("[TTS] VoiceClient未接続のため次の再生をスキップします")
            return
        if not self.audio_queue.empty():
            print("[TTS] 次の音声を再生開始します")
            asyncio.run_coroutine_threadsafe(
                self.play_audio(voice_client), voice_client.loop
            )

    def clear_queue(self):
        """キューをクリア"""
        print("[TTS] キューをクリアします")
        self.audio_queue = asyncio.Queue()
