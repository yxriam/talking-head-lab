#!/usr/bin/env bash
set -euo pipefail

root=/opt/media-models/GenD
python=/opt/media-models/DeepfakeBench/.venv/bin/python
test -x "$python"

# Clone once and reuse the local repository on future runs.
if [ ! -d "$root/.git" ]; then
  git clone --depth 1 https://github.com/yermandy/GenD.git "$root"
fi

"$python" -m pip install transformers==4.56.2 safetensors==0.6.2
install -d /opt/media-models/huggingface

HF_HOME=/opt/media-models/huggingface "$python" - <<'PY'
import sys
from pathlib import Path

root = Path('/opt/media-models/GenD')
sys.path.insert(0, str(root))
from src.hf.modeling_gend import GenD

model = GenD.from_pretrained('yermandy/GenD_CLIP_L_14', cache_dir='/opt/media-models/huggingface')
assert model is not None
print('GEND_MODEL_CACHED')
PY

touch "$root/READY"
echo GEND_INSTALLED
