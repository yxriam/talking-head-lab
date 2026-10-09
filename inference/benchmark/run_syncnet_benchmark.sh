#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)"
sync=/opt/media-models/SyncNet
run="${BENCH_ROOT:-$repo/archive/benchmark-results}/2026-09-23-equal-input"
tmp=/tmp/syncnet-benchmark

for model in sadtalker echomimic_v1 joyvasa echomimic_v3_flash; do
  work="$run/$model"
  cd "$sync"
  .venv/bin/python demo_syncnet.py \
    --initial_model data/syncnet_v2.model \
    --videofile "$work/sync-input.mp4" \
    --tmp_dir "$tmp" --reference "$model" --batch_size 20 --vshift 15 \
    > "$work/syncnet.log" 2>&1
done

"$sync/.venv/bin/python" - "$run" <<'PY'
import json, re, sys
from pathlib import Path

run = Path(sys.argv[1])
summary = {}
for model in ('sadtalker', 'echomimic_v1', 'joyvasa', 'echomimic_v3_flash'):
    text = (run / model / 'syncnet.log').read_text(errors='replace')
    def value(label, cast=float):
        match = re.search(rf'{label}:\s*([-+]?\d+(?:\.\d+)?)', text)
        if not match:
            raise RuntimeError(f'{label} missing for {model}')
        return cast(match.group(1))
    result = {
        'av_offset_frames': value('AV offset', int),
        'lse_d': value('Min dist'),
        'lse_c': value('Confidence'),
    }
    (run / model / 'syncnet-metrics.json').write_text(json.dumps(result, indent=2))
    summary[model] = result
(run / 'syncnet-summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, ensure_ascii=False))
PY
