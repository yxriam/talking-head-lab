#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)"
export PIP_DISABLE_PIP_VERSION_CHECK=1
root=/opt/media-models/DeepfakeBench
test -f /opt/media-models/gpu-verified.json
test -d "$root/.git"

apt-get update
apt-get install -y cmake bzip2
python3 -m venv "$root/.venv"
site="$root/.venv/lib/python3.10/site-packages"
printf '%s\n' /opt/media-models/runtime/lib/python3.10/site-packages > "$site/shared-runtime.pth"
"$root/.venv/bin/python" -m pip install \
  numpy==1.26.4 opencv-python-headless==4.11.0.86 scipy==1.15.3 scikit-image==0.25.2 \
  scikit-learn==1.7.2 imutils==0.5.4 pyyaml==6.0.3 timm==0.9.16 tensorboard==2.20.0 tqdm==4.70.0 \
  dlib==19.24.6
"$root/.venv/bin/python" -c "import cv2,dlib,torch,timm,yaml; assert torch.cuda.is_available()"

# DeepfakeBench imports every training model by default. The local inference
# service registers only the three selected released methods and their losses.
install -m 0644 "$repo/inference/install/detector-runtime/networks-init.py" "$root/training/networks/__init__.py"
install -m 0644 "$repo/inference/install/detector-runtime/detectors-init.py" "$root/training/detectors/__init__.py"
install -m 0644 "$repo/inference/install/detector-runtime/loss-init.py" "$root/training/loss/__init__.py"

mkdir -p "$root/weights"
"$root/.venv/bin/python" - <<'PY'
import bz2
import hashlib
import json
import urllib.request
from pathlib import Path

root = Path('/opt/media-models/DeepfakeBench')
files = {
    f'weights/{name}_best.pth': f'https://github.com/SCLBD/DeepfakeBench/releases/download/v1.0.1/{name}_best.pth'
    for name in ('ucf', 'recce', 'f3net')
}
manifest = []
for filename, url in files.items():
    path = root / filename
    if not path.exists():
        temporary = path.with_suffix(path.suffix + '.part')
        print('Downloading', filename, flush=True)
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest.append({'file':filename, 'source':url, 'sha256':digest})

predictor = root / 'weights/shape_predictor_68_face_landmarks.dat'
predictor_url = 'https://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2'
if not predictor.exists():
    archive = predictor.with_suffix('.dat.bz2')
    temporary = archive.with_suffix(archive.suffix + '.part')
    print('Downloading 68-point face landmark model', flush=True)
    urllib.request.urlretrieve(predictor_url, temporary)
    temporary.replace(archive)
    predictor.write_bytes(bz2.decompress(archive.read_bytes()))
manifest.append({'file':str(predictor.relative_to(root)), 'source':predictor_url,
                 'sha256':hashlib.sha256(predictor.read_bytes()).hexdigest()})
(root / 'weights/download-manifest.json').write_text(json.dumps(manifest,indent=2))
PY
echo DETECTOR_DEPENDENCIES_AND_WEIGHTS_INSTALLED
