#!/bin/sh
set -eu

export DISPLAY="${DISPLAY:-:99}"

Xvfb "$DISPLAY" -screen 0 1280x720x24 -ac +extension GLX +render -noreset &
Xvfb_PID=$!
trap 'kill "$Xvfb_PID" 2>/dev/null || true' EXIT
sleep 1

fluxbox >/tmp/fluxbox.log 2>&1 &
x11vnc -display "$DISPLAY" -forever -shared -nopw -rfbport 5900 >/tmp/x11vnc.log 2>&1 &
websockify --web /usr/share/novnc/ 6080 localhost:5900 >/tmp/websockify.log 2>&1 &

exec gunicorn --bind "0.0.0.0:${PORT:-5000}" --workers 1 --threads 4 app:app
