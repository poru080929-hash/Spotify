FROM python:3.11-slim

# システムパッケージとChromium、ドライバをインストール
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをすべてコピー
COPY . .

# Renderの環境変数PORTに対応してGunicornで起動
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2
