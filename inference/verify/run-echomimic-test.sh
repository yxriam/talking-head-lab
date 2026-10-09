#!/usr/bin/env bash
set -euo pipefail
project="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)"

repo=/opt/media-models/EchoMimic
size=${1:-384}
case "$size" in 256|384|512) ;; *) echo "size must be 256, 384, or 512" >&2; exit 2;; esac
results="${VERIFY_OUT:-$project/archive/verify-output}"; mkdir -p "$results"
out=$results/echomimic-v1-${size}.mp4
log=$results/echomimic-v1-${size}-run.log
gpu=$results/echomimic-v1-${size}-gpu.csv
config=/root/echomimic-v1-local.yaml

cat > "$config" <<'YAML'
pretrained_base_model_path: /opt/media-models/EchoMimic/pretrained_weights/sd-image-variations-diffusers
pretrained_vae_path: /opt/media-models/EchoMimic/pretrained_weights/sd-vae-ft-mse
audio_model_path: /opt/media-models/EchoMimic/pretrained_weights/audio_processor/whisper_tiny.pt
denoising_unet_path: /opt/media-models/EchoMimic/pretrained_weights/denoising_unet_acc.pth
reference_unet_path: /opt/media-models/EchoMimic/pretrained_weights/reference_unet.pth
face_locator_path: /opt/media-models/EchoMimic/pretrained_weights/face_locator.pth
motion_module_path: /opt/media-models/EchoMimic/pretrained_weights/motion_module_acc.pth
inference_config: /opt/media-models/EchoMimic/configs/inference/inference_v2.yaml
weight_dtype: fp16
test_cases:
  /opt/media-app/local-media/data/982bdf07abb44bab86a540ba987024ca/input.jpg:
    - /opt/media-app/local-media/data/9b1ec571abb84408b68cbf153c200b05/output.wav
YAML

printf 'timestamp_ms,memory_used_mib,utilization_gpu_pct\n' > "$gpu"
(
    while true; do
        printf '%s,' "$(date +%s%3N)" >> "$gpu"
        nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits >> "$gpu"
        sleep 0.5
    done
) &
monitor=$!
trap 'kill "$monitor" 2>/dev/null || true' EXIT

cd "$repo"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

set +e
/usr/bin/time -v "$repo/.venv/bin/python" -u infer_audio2vid_acc.py \
    --config "$config" -W "$size" -H "$size" -L 96 --steps 6 --fps 24 --context_frames 12 --context_overlap 3 \
    > "$log" 2>&1
code=$?
set -e
kill "$monitor" 2>/dev/null || true
wait "$monitor" 2>/dev/null || true
trap - EXIT

if [ "$code" -ne 0 ]; then
    echo "ECHOMIMIC_EXIT_CODE=$code"
    tail -n 80 "$log"
    exit "$code"
fi

result=$(find output -type f -name '*withaudio.mp4' -newer "$config" -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
test -n "$result"
cp "$result" "$out"
peak=$(awk -F, 'NR>1 {gsub(/ /,"",$2); if ($2+0>m) m=$2+0} END {print m+0}' "$gpu")
echo "PEAK_GPU_MIB=$peak"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate -show_entries format=duration,size -of json "$out"
echo ECHOMIMIC_TEST_COMPLETE
