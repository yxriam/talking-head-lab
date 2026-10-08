#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/root/autodl-tmp
MT_ROOT="$ROOT/musetalk_baseline/MuseTalk"
ENV_DIR="$ROOT/conda_envs/musetalk_fast"
OUT_ROOT=/root/chatterbox_outputs/musetalk_visa_synthetic_demo
CFG_DIR="$MT_ROOT/configs/inference/autogen_visa_synthetic_demo"
CFG="$CFG_DIR/visa_synthetic_demo.yaml"
RAW_RESULT_NAME=visa_synthetic_demo_musetalk.mp4

mkdir -p "$OUT_ROOT" "$CFG_DIR"
cd "$MT_ROOT"

source /root/miniconda3/etc/profile.d/conda.sh
conda activate "$ENV_DIR"
export LD_LIBRARY_PATH="$ENV_DIR/lib:${LD_LIBRARY_PATH:-}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

python - <<'PY'
from pathlib import Path
import shutil

root = Path("/root/autodl-tmp/musetalk_baseline/MuseTalk")
ms = root / ".modelscope_downloads" / "geekane_musetalk"
models = root / "models"

def copy_if(src, dst):
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or src.stat().st_size != dst.stat().st_size:
            shutil.copy2(src, dst)
            print(f"[FIX] copied {src.relative_to(root)} -> {dst.relative_to(root)}")
    else:
        print(f"[WARN] missing source {src}")

copy_if(ms / "musetalk" / "pytorch_model.bin", models / "musetalk" / "pytorch_model.bin")
copy_if(ms / "musetalk" / "musetalk.json", models / "musetalk" / "musetalk.json")
copy_if(ms / "sd-vae-ft-mse" / "config.json", models / "sd-vae" / "config.json")
copy_if(ms / "sd-vae-ft-mse" / "diffusion_pytorch_model.bin", models / "sd-vae" / "diffusion_pytorch_model.bin")
copy_if(ms / "dwpose" / "dw-ll_ucoco_384.pth", models / "dwpose" / "dw-ll_ucoco_384.pth")
copy_if(ms / "face-parse-bisent" / "79999_iter.pth", models / "face-parse-bisent" / "79999_iter.pth")
copy_if(ms / "face-parse-bisent" / "resnet18-5c106cde.pth", models / "face-parse-bisent" / "resnet18-5c106cde.pth")

path = root / "scripts" / "inference.py"
text = path.read_text()
old = "            shutil.rmtree(save_dir_full)\n            if not args.saved_coord:\n"
new = "            if 'save_dir_full' in locals() and os.path.exists(save_dir_full):\n                shutil.rmtree(save_dir_full)\n            if not args.saved_coord:\n"
if old in text and new not in text:
    path.write_text(text.replace(old, new))
    print("[FIX] patched image-input cleanup")
PY

cat > "$CFG" <<YAML
task_0000:
  video_path: /root/chatterbox_refs/visa.jpg
  audio_path: /root/chatterbox_outputs/visa_synthetic_demo_voice_pcm16.wav
  bbox_shift: 0
  result_name: ${RAW_RESULT_NAME}
YAML

python - <<'PY'
from pathlib import Path
import torch

print("[CHECK] torch", torch.__version__, "cuda", torch.cuda.is_available())
print("[CHECK] gpu", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
for p in [
    "models/musetalk/pytorch_model.bin",
    "models/musetalk/musetalk.json",
    "models/sd-vae/config.json",
    "models/sd-vae/diffusion_pytorch_model.bin",
    "models/whisper/config.json",
    "models/whisper/pytorch_model.bin",
    "models/whisper/preprocessor_config.json",
    "models/dwpose/dw-ll_ucoco_384.pth",
    "models/face-parse-bisent/79999_iter.pth",
    "models/face-parse-bisent/resnet18-5c106cde.pth",
]:
    path = Path(p)
    print("[CHECK]", p, path.exists(), path.stat().st_size if path.exists() else 0)
PY

set +e
python -m scripts.inference \
  --inference_config "$CFG" \
  --result_dir "$OUT_ROOT" \
  --unet_model_path models/musetalk/pytorch_model.bin \
  --unet_config models/musetalk/musetalk.json \
  --version v1 \
  --batch_size 4 \
  --fps 25 \
  --use_float16
code=$?
set -e

if [ "$code" -ne 0 ]; then
  echo "[WARN] fp16 failed with code $code; retrying fp32"
  python -m scripts.inference \
    --inference_config "$CFG" \
    --result_dir "$OUT_ROOT" \
    --unet_model_path models/musetalk/pytorch_model.bin \
    --unet_config models/musetalk/musetalk.json \
    --version v1 \
    --batch_size 2 \
    --fps 25
fi

raw_mp4=$(find "$OUT_ROOT" -type f -name "$RAW_RESULT_NAME" | head -1)
if [ -z "$raw_mp4" ]; then
  echo "[ERROR] raw MuseTalk output not found"
  find "$OUT_ROOT" -type f -printf '%p %s bytes\n' | sort
  exit 2
fi

watermarked="${raw_mp4%.mp4}_watermarked.mp4"
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -y -i "$raw_mp4" \
    -vf "drawtext=text='AI-GENERATED DEMO':x=20:y=20:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.55" \
    -c:a copy "$watermarked" >/tmp/musetalk_watermark.log 2>&1 || cp "$raw_mp4" "$watermarked"
else
  cp "$raw_mp4" "$watermarked"
fi

echo "[DONE] outputs:"
find "$OUT_ROOT" -type f -name '*.mp4' -printf '%p %s bytes\n' | sort
