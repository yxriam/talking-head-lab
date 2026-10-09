#!/usr/bin/env bash
set -euo pipefail

root=/opt/media-models
repo="$root/EchoMimic"

if [ ! -d "$repo/.git" ]; then
    git clone --depth 1 https://github.com/antgroup/echomimic.git "$repo"
else
    echo "REUSED $repo (no git pull)"
fi

python3 -m venv "$repo/.venv"
py="$repo/.venv/bin/python"
"$py" -m pip install --upgrade pip

# EchoMimic pins Torch <=2.2, whose CUDA build cannot execute on this RTX 5070 Ti.
# Keep EchoMimic isolated and use the already verified CUDA 12.8 compatible stack.
"$py" -m pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 \
    --index-url https://download.pytorch.org/whl/cu128
"$py" -m pip install \
    diffusers==0.24.0 transformers==4.45.2 huggingface_hub==0.25.2 \
    accelerate==1.1.1 safetensors mediapipe torchmetrics torchtyping tqdm \
    ffmpeg-python==0.2.0 moviepy==1.0.3 einops==0.4.1 omegaconf==2.3.0 \
    opencv-python-headless 'av>=12' imageio imageio-ffmpeg scipy
"$py" -m pip install facenet-pytorch==2.5.3 --no-deps

"$py" - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="BadToBest/EchoMimic",
    local_dir="/opt/media-models/EchoMimic/pretrained_weights",
    local_dir_use_symlinks=False,
    allow_patterns=[
        "denoising_unet_acc.pth",
        "reference_unet.pth",
        "face_locator.pth",
        "motion_module_acc.pth",
        "sd-vae-ft-mse/**",
        "sd-image-variations-diffusers/**",
        "audio_processor/whisper_tiny.pt",
    ],
)
PY

"$py" - <<'PY'
import torch
assert torch.cuda.is_available()
x = torch.ones((256, 256), device="cuda", dtype=torch.float16)
assert float((x @ x).mean()) == 256.0
print(torch.__version__, torch.cuda.get_device_name(0))
PY

# The official loader briefly holds several float32 copies of multi-GB weights.
# Patch it to construct in fp16 and mmap checkpoints so it fits this WSL machine.
"$py" /opt/media-app/local-media/patch-echomimic-lowmem.py

touch "$repo/READY"
du -sh "$repo" "$repo/pretrained_weights"
echo ECHOMIMIC_V1_ACCELERATED_READY
