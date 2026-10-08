#!/usr/bin/env bash
set -euo pipefail
root=/opt/media-models
app=/opt/media-app/local-media
work=/opt/media-app/verification/voice
test -f "$root/gpu-verified.json"
test -x "$root/chatterbox/.venv/bin/python"
test -f /mnt/d/project/cv/wantanglu_voice_clone_sample.wav
install -d -o alice -g alice "$work"
python3 -c 'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"audio":sys.argv[2],"text":"这是本地音色克隆功能的测试语音。"},ensure_ascii=False),encoding="utf-8")' "$work/request.json" /mnt/d/project/cv/wantanglu_voice_clone_sample.wav
chown alice:alice "$work/request.json"
runuser -u alice -- env HF_HOME="$root/huggingface" HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
  "$root/chatterbox/.venv/bin/python" "$app/generate.py" voice "$work" "$root"
test -s "$work/output.wav"
duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$work/output.wav")
python3 -c 'import sys; value=float(sys.argv[1]); assert 0.2 < value < 60, value' "$duration"
sha256sum "$work/output.wav"
printf 'duration_seconds=%s\n' "$duration"
touch "$root/chatterbox/READY"
echo CHATTERBOX_INFERENCE_VERIFIED
