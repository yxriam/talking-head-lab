#!/usr/bin/env bash
set -euo pipefail
root=/opt/media-models/NPR
if [ ! -d "$root/.git" ]; then
  rm -rf "$root"
  git clone --depth 1 https://github.com/chuangchuangtan/NPR-DeepfakeDetection.git "$root"
fi
test "$(stat -c %s "$root/NPR.pth")" -gt 10000000
/opt/media-models/DeepfakeBench/.venv/bin/python - <<'PY'
import sys, torch
from pathlib import Path
root=Path('/opt/media-models/NPR')
sys.path.insert(0,str(root))
from networks.resnet import resnet50
model=resnet50(num_classes=1)
state=torch.load(root/'NPR.pth',map_location='cpu',weights_only=True)
state=state.get('model',state)
state={key.removeprefix('module.'):value for key,value in state.items()}
model.load_state_dict(state,strict=True)
print('NPR_WEIGHT_VERIFIED',sum(p.numel() for p in model.parameters()))
PY
touch "$root/READY"
