#!/usr/bin/env bash
set -euo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK=1
export HF_HUB_DISABLE_TELEMETRY=1
root=/opt/media-models
mkdir -p "$root"

# All model environments and weights live on the Linux filesystem.
python3 -m venv "$root/runtime"
py="$root/runtime/bin/python"
"$py" -m pip install --upgrade pip
"$py" -m pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
"$py" - <<'PY'
import json, torch
assert torch.cuda.is_available(), 'CUDA is not available'
x = torch.randn(512, 512, device='cuda')
y = x @ x
torch.cuda.synchronize()
assert torch.isfinite(y).all()
result = {'torch':torch.__version__, 'cuda':torch.version.cuda,
          'device':torch.cuda.get_device_name(), 'capability':torch.cuda.get_device_capability(),
          'matrix_test':'passed'}
print(json.dumps(result), flush=True)
open('/opt/media-models/gpu-verified.json','w').write(json.dumps(result))
PY
echo GPU_VERIFIED

for entry in 'chatterbox https://github.com/resemble-ai/chatterbox.git' 'SadTalker https://github.com/OpenTalker/SadTalker.git' 'DeepfakeBench https://github.com/SCLBD/DeepfakeBench.git'; do
    read -r name url <<< "$entry"
    if [ ! -d "$root/$name/.git" ]; then git clone --depth 1 "$url" "$root/$name"; fi
    git -C "$root/$name" rev-parse HEAD
done
echo SOURCES_READY
