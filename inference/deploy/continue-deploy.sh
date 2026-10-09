#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)"
# Stop only the earlier redundant torch installer, then reuse the verified stack.
python3 - <<'PY'
from pathlib import Path
import os, signal
prefix = b'/opt/media-models/chatterbox/.venv/bin/python\x00-m\x00pip\x00install\x00torch==2.7.1\x00'
for process in Path('/proc').glob('[0-9]*'):
    try:
        if (process / 'cmdline').read_bytes().startswith(prefix):
            os.kill(int(process.name), signal.SIGTERM)
            print('Stopped redundant torch installation', process.name, flush=True)
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
PY
sleep 2
out="$repo/archive/inspection"
mkdir -p "$out"
root=/opt/media-models/DeepfakeBench
for name in ucf recce f3net; do
    cp "$root/training/detectors/${name}_detector.py" "$out/"
    cp "$root/training/config/detector/${name}.yaml" "$out/"
done
cp "$root/preprocessing/preprocess.py" "$out/"
cp "$root/training/networks/xception.py" "$out/"
cp "$root/training/loss/__init__.py" "$out/loss-init.py"
# Copy the edited runtime before continuing installation; no Git network calls.
bash "$repo/inference/deploy/sync-runtime.sh"
bash "$repo/inference/install/install-generators.sh"
