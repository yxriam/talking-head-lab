#!/usr/bin/env bash
set -euo pipefail
root=/opt/media-models/SyncNet
shared=/opt/media-models/runtime/lib/python3.10/site-packages
instant=/opt/media-models/InstantID/.venv/lib/python3.10/site-packages

python3 -m venv "$root/.venv"
printf '%s\n%s\n' "$shared" "$instant" > "$root/.venv/lib/python3.10/site-packages/shared-runtime.pth"
"$root/.venv/bin/pip" install python_speech_features==0.6
mkdir -p "$root/data"
if [[ ! -s "$root/data/syncnet_v2.model" ]]; then
  wget -q --show-progress https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model \
    -O "$root/data/syncnet_v2.model"
fi
"$root/.venv/bin/python" - <<'PY'
import cv2
import python_speech_features
import scipy
import torch
print('SYNCNET_READY', torch.__version__)
PY
