#!/usr/bin/env bash
set -euo pipefail

APP=/root/talking_head_webui/app.py
LOG=/root/talking_head_webui/webui.log
PID=/root/talking_head_webui/webui.pid
PORT=${GRADIO_SERVER_PORT:-7860}

if pgrep -f "$APP" >/dev/null; then
  echo "Talking Head WebUI is already running:"
  pgrep -af "$APP"
  exit 0
fi

source /root/miniconda3/etc/profile.d/conda.sh
conda activate /root/autodl-tmp/conda_envs/sadtalker

export GRADIO_ANALYTICS_ENABLED=False
export GRADIO_SERVER_NAME=127.0.0.1
export GRADIO_SERVER_PORT="$PORT"

nohup python "$APP" > "$LOG" 2>&1 &
echo $! > "$PID"
sleep 3
echo "Started Talking Head WebUI on 127.0.0.1:$PORT"
echo "PID: $(cat "$PID")"
tail -40 "$LOG" || true
