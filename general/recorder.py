import discord
import asyncio
import wave
import os
import numpy as np
from io import BytesIO
from collections import defaultdict
import nacl.secret
from discord.ext import commands
from discord.gateway import DiscordVoiceWebSocket
from discord import VoiceClient

##############################################################################
# 1) from_connection_state をパッチして MyVoiceWebSocket を差し込む
##############################################################################
original_from_connection_state = DiscordVoiceWebSocket.from_connection_state


class MyVoiceWebSocket(DiscordVoiceWebSocket):
    def __init__(self, socket, loop):
        super().__init__(socket, loop)
        self.record_ready = False

    async def received_message(self, msg):
        await super().received_message(msg)
        if msg.get("op") == 4:
            print("✅ [MyVoiceWebSocket] OP=4 => record_ready = True")
            self.record_ready = True


@classmethod
async def my_from_connection_state(*args, **kwargs):
    """
    例:
      ライブラリが  DiscordVoiceWebSocket.from_connection_state(self, resume=False, hook=..., ...)
      のように呼んでくる場合、実際には
        args[0] = <class 'discord.gateway.DiscordVoiceWebSocket'>
        args[1] = <discord.voice_state.VoiceConnectionState object>
      などが入る。
    """
    print("⚙️  my_from_connection_state called with:", args, kwargs)

    # 1) 最低限2つの positional arg (cls, state) は必要
    if len(args) < 2:
        raise TypeError("Not enough positional args for from_connection_state")

    # 2) cls と state を取り出し、残りは捨てる
    real_cls = args[0]  # <class 'discord.gateway.DiscordVoiceWebSocket'>
    # <discord.voice_state.VoiceConnectionState object> など
    real_state = args[1]

    # 3) kwargs から不要なものを削除
    kwargs.pop("hook", None)
    kwargs.pop("resume", None)
    kwargs.pop("reconnect", None)
    kwargs.pop("timeout", None)
    # ↑ ライブラリが余計に渡してくる可能性のあるキーワードを片っ端から捨てる

    # 4) オリジナルのクラスメソッドを「__func__」で生呼び出し (バインドを回避)
    ws = await original_from_connection_state.__func__(real_cls, real_state)
    # ↑ これなら positional 引数は 2個 (cls, state) だけになる

    # 5) 生成された ws のクラスを MyVoiceWebSocket にすげ替え
    ws.__class__ = MyVoiceWebSocket
    ws.record_ready = False
    print("🔄 Monkey Patch: DiscordVoiceWebSocket => MyVoiceWebSocket")
    return ws


DiscordVoiceWebSocket.from_connection_state = my_from_connection_state


##############################################################################
# 2) Bot 設定
##############################################################################
TOKEN = os.environ.get("TOKEN_MAN")
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

##############################################################################
# 3) PacketQueue & BufferDecoder
##############################################################################
class PacketQueue:
    def __init__(self):
        self.queues = defaultdict(list)

    def push(self, packet):
        self.queues[packet.ssrc].append(packet)

    def get_all_ssrc(self):
        return list(self.queues.keys())

    def get_packets(self, ssrc: int):
        packets = self.queues.get(ssrc, [])
        while packets:
            yield packets.pop(0)
        yield -1


class BufferDecoder:
    def __init__(self):
        self.queue = PacketQueue()

    def recv_packet(self, packet):
        print(f"📥 パケット受信: SSRC={packet.ssrc}, サイズ={len(packet.decrypted)}")
        self.queue.push(packet)

    async def decode(self):
        file = BytesIO()
        wav = wave.open(file, "wb")
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(48000)

        pcm_list = []
        for ssrc in self.queue.get_all_ssrc():
            arr_list = []
            for packet in self.queue.get_packets(ssrc):
                if packet == -1:
                    break
                arr = np.frombuffer(packet.decrypted, dtype=np.int16)
                if len(arr) % 2 != 0:
                    continue
                arr_list.append(arr.reshape(-1, 2))

            if arr_list:
                combined = np.concatenate(arr_list, axis=0)
                pcm_list.append({"start_time": 0.0, "data": combined})

        if not pcm_list:
            print("⚠️ 録音データがありません。")
            wav.close()
            file.seek(0)
            return file

        pcm_list.sort(key=lambda x: x["start_time"])
        audio_data = np.concatenate([x["data"] for x in pcm_list], axis=0)
        wav.writeframes(audio_data.tobytes())
        wav.close()
        file.seek(0)
        return file


##############################################################################
# 4) カスタム VoiceClient
##############################################################################
class MyVoiceClient(VoiceClient):
    def __init__(self, client, channel):
        super().__init__(client, channel)
        self.record_task = None
        self.decoder = BufferDecoder()
        self.is_recording = False
        print("✅ MyVoiceClient インスタンスが作成されました")

    async def start_recording(self):
        if self.is_recording:
            raise ValueError("既に録音中です。")
        self.is_recording = True
        self.decoder = BufferDecoder()

        if not self.ws:
            print("❌ self.ws が None")
            return

        print("🔍 start_recording: record_ready を待機...")
        for _ in range(50):
            if getattr(self.ws, "record_ready", False):
                break
            print("⏳ record_ready を待機中...")
            await asyncio.sleep(0.1)
        else:
            print("❌ record_ready の準備に失敗")
            return

        print("✅ record_ready=True, 録音開始")
        self.record_task = self.loop.create_task(self._recv_loop())

    async def stop_recording(self):
        if not self.is_recording or self.record_task is None:
            print("🔇 既に録音停止済み")
            return
        self.record_task.cancel()
        self.is_recording = False
        print("🛑 録音タスクキャンセル")

        audio_file = await self.decoder.decode()
        with open("recorded_audio.wav", "wb") as f:
            f.write(audio_file.getvalue())
        print("✅ 録音完了: recorded_audio.wav")

    async def _recv_loop(self):
        while self.is_recording:
            packet = await self.recv_decoded_audio()
            if packet:
                self.decoder.recv_packet(packet)


##############################################################################
# 5) Bot コマンド
##############################################################################
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        try:
            vc = await channel.connect(cls=MyVoiceClient)
            print(f"🎙 '{channel.name}' に参加")
            await vc.start_recording()
        except Exception as e:
            print(f"❌ 参加失敗: {e}")
    else:
        await ctx.send("❌ ボイスチャンネルに接続していません。")


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        vc = ctx.voice_client
        print("🛑 録音停止 & 退出")
        await vc.stop_recording()
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("❌ ボイスチャンネルにいません。")


##############################################################################
# 6) Bot 起動
##############################################################################
if __name__ == "__main__":
    bot.run(TOKEN)
