#!/usr/bin/env bash
set -euo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK=1
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HOME=/opt/media-models/huggingface
root=/opt/media-models
test -f "$root/gpu-verified.json"
test -d "$root/chatterbox/.git"
test -d "$root/SadTalker/.git"

for model in chatterbox SadTalker; do
    python3 -m venv "$root/$model/.venv"
    # Reuse the verified CUDA stack without downloading/copying gigabytes twice.
    site="$root/$model/.venv/lib/python3.10/site-packages"
    printf '%s\n' "$root/runtime/lib/python3.10/site-packages" > "$site/shared-runtime.pth"
    "$root/$model/.venv/bin/python" -c "import torch; assert torch.__version__ == '2.7.1+cu128'"
done

# The upstream torch 2.6 pin predates Blackwell support. Record this local change.
python3 - <<'PY'
from pathlib import Path
p = Path('/opt/media-models/chatterbox/pyproject.toml')
s = p.read_text().replace('torch==2.6.0;', 'torch==2.7.1;').replace('torchaudio==2.6.0;', 'torchaudio==2.7.1;')
p.write_text(s)
PY
"$root/chatterbox/.venv/bin/python" -m pip install -e "$root/chatterbox"
"$root/chatterbox/.venv/bin/python" - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('ResembleAI/chatterbox', allow_patterns=['ve.pt','t3_mtl23ls_v2.safetensors','s3gen.pt','grapheme_mtl_merged_expanded_v1.json','conds.pt','Cangjie5_TC.json'])
PY
echo CHATTERBOX_INSTALLED_NOT_YET_VERIFIED

# The inference service does not need SadTalker's legacy Gradio UI.
sed '/^gradio/d' "$root/SadTalker/requirements.txt" > "$root/SadTalker/requirements-local.txt"
"$root/SadTalker/.venv/bin/python" -m pip install -r "$root/SadTalker/requirements-local.txt"
"$root/SadTalker/.venv/bin/python" - <<'PY'
from pathlib import Path
import site
# basicsr 1.4.2 imports an API moved in newer torchvision.
for folder in site.getsitepackages():
    file = Path(folder) / 'basicsr/data/degradations.py'
    if file.exists():
        file.write_text(file.read_text().replace('torchvision.transforms.functional_tensor','torchvision.transforms.functional'))
PY
cd "$root/SadTalker"
mkdir -p checkpoints gfpgan/weights
"$root/SadTalker/.venv/bin/python" - <<'PY'
import hashlib, json, urllib.request
from pathlib import Path
release = 'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/'
files = {f'checkpoints/{name}': release + name for name in ['mapping_00109-model.pth.tar','mapping_00229-model.pth.tar','SadTalker_V0.0.2_256.safetensors']}
files.update({
 'gfpgan/weights/alignment_WFLW_4HG.pth':'https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth',
 'gfpgan/weights/detection_Resnet50_Final.pth':'https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth',
 'gfpgan/weights/parsing_parsenet.pth':'https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth'})
manifest = []
for filename, url in files.items():
    path = Path(filename)
    if not path.exists():
        print('Downloading',filename,flush=True)
        temporary = path.with_suffix(path.suffix + '.part')
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(path)
    manifest.append({'file':filename,'source':url,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()} if hasattr(hashlib,'file_digest') else {'file':filename,'source':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
Path('download-manifest.json').write_text(json.dumps(manifest,indent=2))
PY
echo SADTALKER_INSTALLED_NOT_YET_VERIFIED
