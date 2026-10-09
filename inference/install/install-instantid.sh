#!/usr/bin/env bash
set -euo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK=1
export HF_HUB_DISABLE_TELEMETRY=1
# The parallel Rust downloader is fast, but Tencent/WSL connections can exhaust
# its permit pool on multi-gigabyte files. The standard downloader resumes the
# same partial files and is much more reliable here.
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HOME=/opt/media-models/huggingface
root=/opt/media-models/InstantID
shared=/opt/media-models/runtime/lib/python3.10/site-packages

if [[ ! -d "$root/.git" ]]; then
    git clone --depth 1 https://github.com/instantX-research/InstantID.git "$root"
fi
python3 -m venv "$root/.venv"
printf '%s\n' "$shared" > "$root/.venv/lib/python3.10/site-packages/shared-runtime.pth"
"$root/.venv/bin/pip" install \
    numpy==1.26.4 Pillow==10.3.0 opencv-python==4.10.0.84 insightface==0.7.3 \
    onnxruntime accelerate==0.28.0 diffusers==0.27.2 transformers==4.39.2 \
    huggingface-hub==0.25.2 hf-transfer==0.1.9 safetensors==0.4.5 einops==0.8.0 \
    omegaconf==2.3.0 peft==0.10.0 rembg==2.0.67

if ! command -v aria2c >/dev/null || ! command -v unzip >/dev/null; then
    apt-get update -qq
    apt-get install -y -qq aria2 unzip
fi

fetch_large() {
    local repo="$1" file="$2" destination="$3"
    mkdir -p "$(dirname "$destination")"
    aria2c -c -x 16 -s 16 -k 4M --file-allocation=none --console-log-level=warn \
        --connect-timeout=30 --timeout=60 --max-tries=20 --retry-wait=3 \
        -d "$(dirname "$destination")" -o "$(basename "$destination")" \
        "https://huggingface.co/${repo}/resolve/main/${file}"
}

weights="$root/weights"
fetch_large InstantX/InstantID ControlNetModel/diffusion_pytorch_model.safetensors \
    "$weights/instantid/ControlNetModel/diffusion_pytorch_model.safetensors"
fetch_large InstantX/InstantID ip-adapter.bin "$weights/instantid/ip-adapter.bin"
fetch_large stabilityai/stable-diffusion-xl-base-1.0 text_encoder/model.fp16.safetensors \
    "$weights/sdxl-base/text_encoder/model.fp16.safetensors"
fetch_large stabilityai/stable-diffusion-xl-base-1.0 text_encoder_2/model.fp16.safetensors \
    "$weights/sdxl-base/text_encoder_2/model.fp16.safetensors"
fetch_large stabilityai/stable-diffusion-xl-base-1.0 unet/diffusion_pytorch_model.fp16.safetensors \
    "$weights/sdxl-base/unet/diffusion_pytorch_model.fp16.safetensors"
fetch_large stabilityai/stable-diffusion-xl-base-1.0 vae/diffusion_pytorch_model.fp16.safetensors \
    "$weights/sdxl-base/vae/diffusion_pytorch_model.fp16.safetensors"
fetch_large latent-consistency/lcm-lora-sdxl pytorch_lora_weights.safetensors \
    "$weights/lcm/pytorch_lora_weights.safetensors"

"$root/.venv/bin/python" - <<'PY'
from huggingface_hub import hf_hub_download, snapshot_download
from pathlib import Path

root = Path('/opt/media-models/InstantID/weights')
instant = root / 'instantid'
for filename in ('ControlNetModel/config.json',):
    hf_hub_download('InstantX/InstantID', filename=filename, local_dir=instant)
snapshot_download('stabilityai/stable-diffusion-xl-base-1.0', local_dir=root / 'sdxl-base',
                  allow_patterns=['model_index.json', 'scheduler/**', 'tokenizer/**', 'tokenizer_2/**',
                                  'text_encoder/config.json', 'text_encoder_2/config.json',
                                  'unet/config.json', 'vae/config.json'])
PY

mkdir -p "$root/models"
if [[ ! -f "$root/models/antelopev2/glintr100.onnx" ]]; then
    "$root/.venv/bin/pip" install gdown==5.2.0
    "$root/.venv/bin/gdown" --fuzzy \
        'https://drive.google.com/file/d/18wEUfMNohBJ4K3Ly5wpTejPfDzp-8fI8/view?usp=sharing' \
        -O "$root/models/antelopev2.zip"
    unzip -qo "$root/models/antelopev2.zip" -d "$root/models"
fi
rm -f "$root/READY"
mkdir -p "$weights/rembg"
U2NET_HOME="$weights/rembg" "$root/.venv/bin/python" - <<'PY'
from rembg import new_session
new_session('u2net_human_seg')
PY
chmod -R a+rX "$weights/rembg"
touch "$root/WEIGHTS_READY"
echo INSTANTID_WEIGHTS_READY
