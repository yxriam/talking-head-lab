#!/usr/bin/env bash
set -euo pipefail
run=${1:-/mnt/d/project/NZ/cv/benchmark-results/2026-09-24-multi-sample}
sync=/opt/media-models/SyncNet
tmp=/tmp/syncnet-multi

for work in "$run"/cases/*/{sadtalker,echomimic_v1,joyvasa,echomimic_v3_flash}; do
  [[ -s "$work/sync-input.mp4" ]] || continue
  [[ -s "$work/syncnet-metrics.json" ]] && continue
  ref="$(basename "$(dirname "$work")")_$(basename "$work")"
  cd "$sync"
  .venv/bin/python demo_syncnet.py --initial_model data/syncnet_v2.model \
    --videofile "$work/sync-input.mp4" --tmp_dir "$tmp" --reference "$ref" \
    --batch_size 20 --vshift 15 > "$work/syncnet.log" 2>&1
  .venv/bin/python - "$work" <<'PY'
import json,re,sys
from pathlib import Path
w=Path(sys.argv[1]); text=(w/'syncnet.log').read_text(errors='replace')
def v(label,cast=float):
    m=re.search(rf'{label}:\s*([-+]?\d+(?:\.\d+)?)',text)
    if not m: raise RuntimeError(label)
    return cast(m.group(1))
(w/'syncnet-metrics.json').write_text(json.dumps({'av_offset_frames':v('AV offset',int),'lse_d':v('Min dist'),'lse_c':v('Confidence')},indent=2))
PY
  echo "SYNC $ref"
done
