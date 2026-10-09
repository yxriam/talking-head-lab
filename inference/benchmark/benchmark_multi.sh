#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)"

run_root="${1:-$repo/archive/benchmark-results/2026-09-24-multi-sample}"
models=/opt/media-models
app=/opt/media-app/local-media
# V3 Flash was attempted on five independent cases and was killed during model
# loading every time on this host. Continue the remaining cases with the three
# models that can complete, while preserving the failed V3 attempts as evidence.
model_names=(sadtalker echomimic_v1 joyvasa)

python_for() {
  case "$1" in
    sadtalker) echo "$models/SadTalker/.venv/bin/python" ;;
    echomimic_v1) echo "$models/EchoMimic/.venv/bin/python" ;;
    joyvasa) echo "$models/JoyVASA/.venv/bin/python" ;;
    echomimic_v3_flash) echo "$models/EchoMimicV3/.venv/bin/python" ;;
  esac
}

for case_dir in "$run_root"/cases/*; do
  [[ -d "$case_dir" ]] || continue
  case_id=$(basename "$case_dir")
  for model in "${model_names[@]}"; do
    work="$case_dir/$model"
    if [[ -s "$work/output.mp4" && -s "$work/performance.json" ]]; then
      echo "SKIP $case_id $model"
      continue
    fi
    mkdir -p "$work"
    cp "$case_dir/input.png" "$work/input.png"
    cp "$case_dir/input.wav" "$work/input.wav"
    cat > "$work/request.json" <<JSON
{"kind":"video","model":"$model","image":"$work/input.png","audio":"$work/input.wav","scene":"benchmark"}
JSON
    nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv,noheader,nounits -lms 250 > "$work/gpu.csv" &
    monitor=$!
    started=$(date +%s.%N)
    set +e
    /usr/bin/time -v -o "$work/time.txt" "$(python_for "$model")" "$app/generate.py" video "$work" "$models" > "$work/model.log" 2>&1
    status=$?
    set -e
    finished=$(date +%s.%N)
    kill "$monitor" 2>/dev/null || true

    "$models/runtime/bin/python" - "$work" "$model" "$started" "$finished" "$status" <<'PY'
import csv, json, re, subprocess, sys
from pathlib import Path
work, model, started, finished, status = Path(sys.argv[1]), sys.argv[2], *sys.argv[3:]
time_text = (work/'time.txt').read_text(errors='replace') if (work/'time.txt').exists() else ''
rss = re.search(r'Maximum resident set size \(kbytes\): (\d+)', time_text)
gpu=[]
if (work/'gpu.csv').exists():
    for row in csv.reader((work/'gpu.csv').open(errors='replace')):
        try: gpu.append(int(row[1].strip()))
        except (ValueError,IndexError): pass
result={'model':model,'exit_code':int(status),'wall_seconds':round(float(finished)-float(started),3),
        'max_rss_mb':round(int(rss.group(1))/1024,1) if rss else None,'peak_gpu_memory_mb':max(gpu,default=None)}
out=work/'output.mp4'
if out.exists():
    result['output']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate','-of','json',str(out)],text=True))
(work/'performance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
PY
    echo "DONE $case_id $model status=$status seconds=$(python3 -c "import json;print(json.load(open('$work/performance.json'))['wall_seconds'])")"
  done
done
