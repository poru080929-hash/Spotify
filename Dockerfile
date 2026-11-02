FROM python:3.11-slim

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

# 起動コマンド：Xvfb、x11vnc、websockifyをバックグラウンドで起動し、Pythonアプリを実行
CMD ["sh", "-c", "\
Xvfb :99 -screen 0 1280x720x16 & \
export DISPLAY=:99 && \
sleep 1 && \
x11vnc -display :99 -forever -shared -nopw & \
websockify --web /usr/share/novnc/ 6080 localhost:5900 & \
exec python app.py \
"]
