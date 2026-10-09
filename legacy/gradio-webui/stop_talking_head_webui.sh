#!/usr/bin/env bash
set -euo pipefail

APP=/root/talking_head_webui/app.py

if pgrep -f "$APP" >/dev/null; then
  pkill -f "$APP"
  echo "Stopped Talking Head WebUI."
else
  echo "Talking Head WebUI is not running."
fi
