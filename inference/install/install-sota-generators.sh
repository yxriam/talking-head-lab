#!/usr/bin/env bash
set -euo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK=1
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HOME=/opt/media-models/huggingface
root=/opt/media-models
shared="$root/runtime/lib/python3.10/site-packages"

if [[ ! -d "$root/JoyVASA/.git" ]]; then
    git clone --depth 1 https://github.com/jdh-algo/JoyVASA.git "$root/JoyVASA"
fi
if [[ ! -d "$root/EchoMimicV3/.git" ]]; then
    git clone --depth 1 https://github.com/antgroup/echomimic_v3.git "$root/EchoMimicV3"
fi

make_env() {
    local name="$1"
    python3 -m venv "$root/$name/.venv"
    printf '%s\n' "$shared" > "$root/$name/.venv/lib/python3.10/site-packages/shared-runtime.pth"
    "$root/$name/.venv/bin/python" -c "import torch; assert torch.__version__ == '2.7.1+cu128'"
}

make_env JoyVASA
"$root/JoyVASA/.venv/bin/pip" install \
    huggingface_hub accelerate==0.28.0 av==12.1.0 decord==0.6.0 diffusers==0.27.2 \
    einops==0.8.0 insightface==0.7.3 librosa==0.10.2.post1 mediapipe==0.10.14 \
    moviepy==1.0.3 numpy==1.26.4 omegaconf==2.3.0 onnx==1.16.1 \
    onnxruntime-gpu opencv-python==4.10.0.84 pillow==10.3.0 pyyaml==6.0.1 \
    scipy==1.13.1 imageio==2.34.2 lmdb==1.4.1 rich==13.7.1 ffmpeg-python==0.2.0 \
    scikit-image==0.24.0 albumentations==1.4.10 matplotlib==3.9.0 \
    imageio-ffmpeg==0.5.1 tyro==0.8.5 pykalman==0.9.7 transformers==4.39.2
"$root/JoyVASA/.venv/bin/python" - <<'PY'
from huggingface_hub import snapshot_download
from pathlib import Path
root = Path('/opt/media-models/JoyVASA/pretrained_weights')
root.mkdir(exist_ok=True)
snapshot_download('jdh-algo/JoyVASA', local_dir=root / 'JoyVASA')
snapshot_download('KwaiVGI/LivePortrait', local_dir=root,
                  allow_patterns=['insightface/**', 'liveportrait/**'])
snapshot_download('TencentGameMate/chinese-hubert-base', local_dir=root / 'chinese-hubert-base')
PY
ln -sfn chinese-hubert-base "$root/JoyVASA/pretrained_weights/TencentGameMate:chinese-hubert-base"
sed -i 's/torch.load(ckpt_path, map_location=device)/torch.load(ckpt_path, map_location=device, weights_only=False)/' \
    "$root/JoyVASA/src/utils/helper.py"
touch "$root/JoyVASA/READY"
echo JOYVASA_READY

make_env EchoMimicV3
"$root/EchoMimicV3/.venv/bin/pip" install \
    Pillow einops safetensors timm tomesd torchdiffeq torchsde decord \
    numpy scikit-image opencv-python omegaconf SentencePiece albumentations \
    'imageio[ffmpeg,pyav]' beautifulsoup4 ftfy func_timeout onnxruntime \
    accelerate==1.1.1 diffusers==0.31.0 transformers==4.46.2 huggingface_hub==0.26.2 \
    moviepy==2.2.1 librosa pyloudnorm
"$root/EchoMimicV3/.venv/bin/python" - <<'PY'
from huggingface_hub import snapshot_download
from pathlib import Path
root = Path('/opt/media-models/EchoMimicV3/weights')
root.mkdir(exist_ok=True)
snapshot_download('alibaba-pai/Wan2.1-Fun-V1.1-1.3B-InP', local_dir=root / 'Wan2.1-Fun-V1.1-1.3B-InP')
snapshot_download('BadToBest/EchoMimicV3', local_dir=root / 'flash',
                  allow_patterns=['echomimicv3-flash-pro/**'])
snapshot_download('TencentGameMate/chinese-wav2vec2-base', local_dir=root / 'chinese-wav2vec2-base')
PY
"$root/EchoMimicV3/.venv/bin/python" - <<'PY'
from pathlib import Path
path = Path('/opt/media-models/EchoMimicV3/infer_flash.py')
text = path.read_text()
old = '    pipeline.to(device=device)'
replacement = '''    if GPU_memory_mode == "sequential_cpu_offload":
        pipeline.enable_sequential_cpu_offload()
    else:
        pipeline.to(device=device)'''
if 'pipeline.enable_sequential_cpu_offload()' not in text:
    if text.count(old) != 2:
        raise RuntimeError('Unexpected EchoMimic V3 pipeline layout')
    text = text.replace(old, replacement, 1)
    marker = '\n    pipeline.to(device=device)\n\n    # Create output directory'
    if marker not in text:
        raise RuntimeError('Unexpected EchoMimic V3 second device placement')
    text = text.replace(marker, '\n    # Device placement is configured above.\n\n    # Create output directory', 1)
old_mux = 'video_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", threads=2)'
new_mux = 'video_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", threads=2, temp_audiofile=os.path.join(save_path, f"{image_name}_audio.m4a"))'
if old_mux in text:
    text = text.replace(old_mux, new_mux, 1)
elif new_mux not in text:
    raise RuntimeError('Unexpected EchoMimic V3 audio mux layout')
path.write_text(text)
PY
"$root/EchoMimicV3/.venv/bin/python" \
    /opt/media-app/local-media/patch_echomimic_v3_memory.py \
    "$root/EchoMimicV3/infer_flash.py"
rm -f "$root/EchoMimicV3/READY"
touch "$root/EchoMimicV3/WEIGHTS_READY"
echo ECHOMIMIC_V3_WEIGHTS_READY
