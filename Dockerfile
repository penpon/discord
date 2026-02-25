# Pythonの公式軽量イメージを使用
FROM python:3.11-slim

# タイムゾーンと環境変数の設定
ENV TZ=Asia/Tokyo
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリの設定
WORKDIR /app

# 必要なシステムパッケージ (ffmpeg, libsodium等) をインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg git build-essential \
    libsodium-dev libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーしてパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードとアセットをコピー
COPY bot/ /app/bot/
COPY assets/ /app/assets/

# (必要に応じて) data ディレクトリを作成
RUN mkdir -p /app/data

# 実行コマンド
CMD ["python", "bot/main.py"]
