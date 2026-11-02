FROM python:3.11-slim

# システムパッケージ、Chromium、XFCEデスクトップ、VNC、noVNCをインストール
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    x11vnc \
    fluxbox \
    net-tools \
    curl \
    wget \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 起動時にXvfb（仮想画面）、x11vnc、websockify、そしてFlaskアプリをまとめて起動するスクリプトを指定
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x720x16 & export DISPLAY=:99 && x11vnc -display :99 -forever -nopw & websockify --web /usr/share/novnc/ 6080 localhost:5900 & python app.py --bind 0.0.0.0:$PORT"]
