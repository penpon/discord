import io
import logging
import asyncio

from gtts import gTTS
from discord import FFmpegPCMAudio

logger = logging.getLogger(__name__)


class TTSHandler:
    def __init__(self):
        logger.info("[TTS] TTSハンドラーを初期化します")
        self.audio_queue: asyncio.Queue = asyncio.Queue()

    def _synthesize_tts(self, text: str) -> io.BytesIO:
        """同期処理: gTTSで音声を生成（スレッドにオフロードして呼び出す）"""
        tts = gTTS(text=text, lang="ja")
        audio_data = io.BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)
        return audio_data

    async def generate_tts(
        self, text: str, speed: float = 1.0, ffmpeg_filter: str = None
    ):
        """TTS音声の生成とキュー追加"""
        logger.info(f"[TTS] 音声生成: {text[:20]}... (速度: {speed}x)")
        try:
            # gTTSは同期I/Oのためイベントループをブロックしないようスレッドにオフロード
            audio_data = await asyncio.to_thread(self._synthesize_tts, text)
            await self.audio_queue.put((audio_data, speed, ffmpeg_filter))
            logger.debug(
                f"[TTS] キューに追加（現在のキューサイズ: {self.audio_queue.qsize()}）"
            )
        except Exception as e:
            logger.error(f"[TTS ERROR] 音声生成に失敗しました: {e}")
            # フォールバック: 失敗した場合は無音（キューには積まない）

    async def play_audio(self, voice_client):
        """音声再生のメイン処理"""
        logger.debug("[TTS] 音声再生処理を開始します")
        if (
            not getattr(voice_client, "is_connected", None)
            or not voice_client.is_connected()
        ):
            logger.warning("[TTS] VoiceClientが未接続のため再生を中止します")
            return
        while not self.audio_queue.empty():
            if voice_client.is_playing():
                await asyncio.sleep(0.5)
                continue

            audio_data, speed, ffmpeg_filter = await self.audio_queue.get()
            try:
                filter_chain = []
                if ffmpeg_filter:
                    filter_chain.append(ffmpeg_filter)
                if speed != 1.0:
                    filter_chain.append(f"atempo={speed}")
                options = f"-af {','.join(filter_chain)}" if filter_chain else ""

                logger.debug(f"[TTS] 再生開始（速度: {speed}x, options: {options}）")
                voice_client.play(
                    FFmpegPCMAudio(
                        audio_data, pipe=True, options=options if options else None
                    ),
                    after=lambda e: self._queue_next(voice_client),
                )
            except Exception as e:
                logger.error(f"[TTS ERROR] 再生中にエラーが発生しました: {e}")

    def _queue_next(self, voice_client):
        """次の音声を再生するためのコールバック"""
        if (
            not getattr(voice_client, "is_connected", None)
            or not voice_client.is_connected()
        ):
            return
        if not self.audio_queue.empty():
            asyncio.run_coroutine_threadsafe(
                self.play_audio(voice_client), voice_client.loop
            )

    def clear_queue(self):
        """キューをクリア"""
        logger.info("[TTS] キューをクリアします")
        self.audio_queue = asyncio.Queue()
