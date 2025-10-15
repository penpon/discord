# Discord Bot

このDiscord Botは音声読み上げ機能とポケモン関連機能を提供します。

## 機能一覧

### 現在有効な機能

#### 音声読み上げ (TTS)
- ボイスチャンネルでのテキスト読み上げ
- 入退室時の音声通知（1.3倍速）
- URLや長い数字を含むメッセージの自動フィルタリング
- **ユーザー別TTSプロファイル機能**（6種類のボイスエフェクト）

#### ボイスチャンネル管理
- `$join` - ボイスチャンネルに参加
- `$leave` - ボイスチャンネルから退出
- `$play とにかくやれ` - 特定の音声ファイルを再生

#### TTSプロファイル管理（特定ユーザー限定）
- `$tts_profile_set @ユーザー <0-5>` - ユーザーにTTSプロファイルを割当
  - 0: デフォルト（フィルタなし）
  - 1: ユーザー1（明瞭・ニュース調）
  - 2: ユーザー2（明るめ・速め）
  - 3: ユーザー3（低め・標準速度）
  - 4: ユーザー4（やや高め・やや速め）
  - 5: ユーザー5（暗め・遅め）
- `$tts_profile_clear @ユーザー` - プロファイル割当を削除（デフォルトに戻す）
- `$tts_profile_show [@ユーザー]` - 現在のプロファイルを確認（省略時は自分、全員利用可）
- `$tts_profile_list` - 全ユーザーのプロファイル割当一覧を表示

#### その他のコマンド
- `$clear_bot [数]` - BOTのメッセージを指定数削除（特定ユーザー限定）

#### ポケモン機能
- ポケモン関連のクイズ機能
- ポケモン画像の管理

### 現在無効化されている機能

#### hayato_api (RAG機能)
- BOTへのメンション応答機能
- ベクトルDBを使用した文脈を考慮した返答
- AIによる会話応答機能

**注意**: hayato_api関連の全ての機能は現在コメントアウトされており、BOTにメンション（@ボット名）を送っても反応しません。

## プロジェクト構造

```
discord/
├── general/              # 汎用スクリプト
├── pokemon/             # ポケモン関連機能
│   ├── cogs/           # ポケモンBot用Cogs
│   └── pokemon_jpg/    # ポケモン画像
├── text_read/          # TTS機能
│   ├── cogs/          # TTS Bot用Cogs
│   │   ├── hayato_api.py    # (無効化) RAG機能
│   │   ├── main_cog.py      # メインのCog
│   │   └── tts_handler.py   # TTS処理
│   └── sounds/        # 音声ファイル
└── requirements.txt    # 依存関係
```

## セットアップ

1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

2. 環境変数の設定
- Discord Bot Token
- OpenAI API Key (hayato_api使用時)
- ElevenLabs API Key (高品質TTS使用時)

3. Botの起動
```bash
# TTS Bot
python text_read/main.py

# ポケモンBot
python pokemon/main.py
```