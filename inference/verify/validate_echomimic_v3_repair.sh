#!/usr/bin/env bash
set -euo pipefail

work=${1:?work directory required}
image=${2:?image required}
audio=${3:?audio required}
models=/opt/media-models
app=/opt/media-app/local-media
python="$models/EchoMimicV3/.venv/bin/python"

mkdir -p "$work"
cp "$image" "$work/input.png"
cp "$audio" "$work/input.wav"
cat > "$work/request.json" <<JSON
{"kind":"video","model":"echomimic_v3_flash","image":"$work/input.png","audio":"$work/input.wav","scene":"repair_validation"}
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

"$models/runtime/bin/python" - "$work" "$started" "$finished" "$status" <<'PY'
import csv, json, re, subprocess, sys
from pathlib import Path
work, started, finished, status = Path(sys.argv[1]), *sys.argv[2:]
time_text = (work/'time.txt').read_text(errors='replace') if (work/'time.txt').exists() else ''
rss = re.search(r'Maximum resident set size \(kbytes\): (\d+)', time_text)
gpu_mem=[]; gpu_util=[]
if (work/'gpu.csv').exists():
    for row in csv.reader((work/'gpu.csv').open(errors='replace')):
        try: gpu_mem.append(int(row[1].strip())); gpu_util.append(int(row[2].strip()))
        except (ValueError,IndexError): pass
result={'model':'echomimic_v3_flash','exit_code':int(status),
        'wall_seconds':round(float(finished)-float(started),3),
        'max_rss_mb':round(int(rss.group(1))/1024,1) if rss else None,
        'peak_gpu_memory_mb':max(gpu_mem,default=None),
        'mean_gpu_util_percent':round(sum(gpu_util)/len(gpu_util),1) if gpu_util else None}
out=work/'output.mp4'
if out.exists():
    result['output']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate','-of','json',str(out)],text=True))
(work/'performance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
PY
exit "$status"
