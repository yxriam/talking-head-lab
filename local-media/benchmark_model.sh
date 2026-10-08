#!/usr/bin/env bash
set -euo pipefail

model="${1:?model is required}"
run_root=/mnt/d/project/NZ/cv/benchmark-results/2026-09-23-equal-input
work="$run_root/$model"
image=/mnt/d/project/NZ/cv/local-media/preserved-scene-output.png
audio=/mnt/d/project/NZ/cv/local-media/integration-audio.wav
models=/opt/media-models
app=/opt/media-app/local-media

case "$model" in
  sadtalker) python="$models/SadTalker/.venv/bin/python" ;;
  echomimic_v1) python="$models/EchoMimic/.venv/bin/python" ;;
  joyvasa) python="$models/JoyVASA/.venv/bin/python" ;;
  echomimic_v3_flash) python="$models/EchoMimicV3/.venv/bin/python" ;;
  *) echo "unknown model: $model" >&2; exit 2 ;;
esac

if [[ -e "$work" ]]; then
  echo "benchmark directory already exists: $work" >&2
  exit 3
fi
mkdir -p "$work"
cp "$image" "$work/input.png"
cp "$audio" "$work/input.wav"
cat > "$work/request.json" <<JSON
{"kind":"video","model":"$model","image":"$work/input.png","audio":"$work/input.wav","scene":"professional_office"}
JSON

nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv,noheader,nounits -lms 250 > "$work/gpu.csv" &
monitor=$!
cleanup() { kill "$monitor" 2>/dev/null || true; }
trap cleanup EXIT

started=$(date +%s.%N)
set +e
/usr/bin/time -v -o "$work/time.txt" "$python" "$app/generate.py" video "$work" "$models" > "$work/model.log" 2>&1
status=$?
set -e
finished=$(date +%s.%N)
cleanup
trap - EXIT

"$models/runtime/bin/python" - "$work" "$model" "$started" "$finished" "$status" <<'PY'
import csv, json, re, subprocess, sys
from pathlib import Path

work, model, started, finished, status = Path(sys.argv[1]), sys.argv[2], *sys.argv[3:]
time_text = (work / 'time.txt').read_text(errors='replace')
rss = re.search(r'Maximum resident set size \(kbytes\): (\d+)', time_text)
gpu_memory, gpu_util = [], []
with (work / 'gpu.csv').open(newline='', errors='replace') as handle:
    for row in csv.reader(handle):
        if len(row) >= 3:
            try:
                gpu_memory.append(int(row[1].strip()))
                gpu_util.append(int(row[2].strip()))
            except ValueError:
                pass
result = {
    'model': model,
    'exit_code': int(status),
    'wall_seconds': round(float(finished) - float(started), 3),
    'max_rss_mb': round(int(rss.group(1)) / 1024, 1) if rss else None,
    'peak_gpu_memory_mb': max(gpu_memory, default=None),
    'mean_gpu_util_percent': round(sum(gpu_util) / len(gpu_util), 1) if gpu_util else None,
}
output = work / 'output.mp4'
if output.exists():
    probe = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type,width,height,r_frame_rate', '-of', 'json', str(output)
    ], text=True)
    result['output'] = json.loads(probe)
(work / 'performance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False))
PY
exit "$status"
