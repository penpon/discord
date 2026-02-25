# Discord TTS Bot

Discord ボイスチャンネルでのテキスト読み上げ（TTS）機能を提供するBotです。

## 機能一覧

### 音声読み上げ (TTS)
- ボイスチャンネル接続中のテキスト自動読み上げ
- 入退室時の音声通知（1.3倍速）
- URLや長い数字を含むメッセージのフィルタリング
- ユーザー別TTSプロファイル機能（4種類のボイスエフェクト）

### ボイスチャンネル管理
- `$join` - ボイスチャンネルに参加
- `$leave` - ボイスチャンネルから退出
- `$play <名前>` - 特定の音声ファイルを再生（例: `$play はやね`）

### その他
- `$clear_bot [数]` - BOTのメッセージを指定数削除（管理者限定）

## プロジェクト構造

```
discord/
├── bot/                    # Botアプリケーション本体
│   ├── main.py             # エントリポイント
│   ├── cogs/               # Discordコマンド定義
│   │   ├── general.py
│   │   ├── main_cog.py
│   │   └── voice_commands.py
│   └── core/               # ビジネスロジック・インフラ層
│       ├── config.py
│       ├── database.py
│       └── tts_handler.py
├── assets/                 # 音声アセット（Git管理外）
│   └── sounds/
├── data/                   # データベース永続化領域（Git管理外）
│   └── messages.db
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## セットアップ

### 環境変数の設定

`.env.example` をコピーして `.env` を作成し、各値を設定します。

```bash
cp .env.example .env
```

| 変数名 | 説明 |
|---|---|
| `TOKEN_NU` | Discord Bot Token |
| `ADMIN_USER_ID` | 管理者コマンドを実行できるユーザーID |
| `TZ` | タイムゾーン (デフォルト: Asia/Tokyo) |

### Dockerで起動（推奨）

```bash
docker compose up --build
```

### ローカルで起動

```bash
pip install -r requirements.txt
python bot/main.py
```

> **Note**: `assets/sounds/` ディレクトリに必要な音声ファイルを配置してください（Dockerを使用する場合はビルド時に自動コピーされます）。