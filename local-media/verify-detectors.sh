#!/usr/bin/env bash
set -euo pipefail
root=/opt/media-models/DeepfakeBench
app=/opt/media-app/local-media
work=/opt/media-app/verification/detect
video=/opt/media-app/verification/video/output.mp4
test -x "$root/.venv/bin/python"
test -s "$video"
bash /mnt/d/project/cv/local-media/sync-runtime.sh
install -d -o alice -g alice "$work"
runuser -u alice -- "$root/.venv/bin/python" "$app/detect.py" "$video" "$root" "$work/generated-report.json"
"$root/.venv/bin/python" -c 'import json,math,sys; r=json.load(open(sys.argv[1])); assert {m["id"] for m in r["methods"]}=={"gend","npr","ucf","recce","f3net"}; assert all(m["status"]=="done" and math.isfinite(m["ai_probability"]) and math.isclose(m["ai_probability"]+m["real_probability"],1,abs_tol=1e-6) for m in r["methods"]); assert r["summary"]["passed"]+r["summary"]["failed"]==5' "$work/generated-report.json"
touch "$root/READY"
cat "$work/generated-report.json"
echo FIVE_DETECTORS_INFERENCE_VERIFIED
