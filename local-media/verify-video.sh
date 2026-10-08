#!/usr/bin/env bash
set -euo pipefail
root=/opt/media-models
app=/opt/media-app/local-media
work=/opt/media-app/verification/video
image=/mnt/d/project/cv/facebook-scam/data/accounts/01_ray_hunt/original_media/images/0004_514620660_10238630792254422_420361085077167201_n.jpg
audio=/opt/media-app/verification/voice/output.wav
test -f "$root/gpu-verified.json"
bash /mnt/d/project/cv/local-media/sync-runtime.sh
test -f "$root/chatterbox/READY"
test -x "$root/SadTalker/.venv/bin/python"
test -s "$image"
test -s "$audio"
install -d -o alice -g alice "$work"
python3 -c 'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"image":sys.argv[2],"audio":sys.argv[3]}),encoding="utf-8")' "$work/request.json" "$image" "$audio"
chown alice:alice "$work/request.json"
runuser -u alice -- env TORCH_HOME=/opt/media-models/torch-cache \
  "$root/SadTalker/.venv/bin/python" "$app/generate.py" video "$work" "$root"
test -s "$work/output.mp4"
duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$work/output.mp4")
python3 -c 'import sys; value=float(sys.argv[1]); assert 0.2 < value < 60, value' "$duration"
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height -of default=nw=1 "$work/output.mp4"
sha256sum "$work/output.mp4"
printf 'duration_seconds=%s\n' "$duration"
touch "$root/SadTalker/READY"
echo SADTALKER_INFERENCE_VERIFIED
