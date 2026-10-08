"""Build a local detector score table from explicitly labelled media.

The script never reads media metadata to classify a request. Generation job
metadata is used only offline to assemble the positive calibration set.
"""

import argparse
import json
import subprocess
from pathlib import Path


def generated_videos(data):
    for directory in sorted(data.iterdir()):
        try:
            job = json.loads((directory / "job.json").read_text(encoding="utf-8"))
            media = json.loads((directory / "media.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        path = directory / media.get("filename", "")
        if job.get("kind") == "video" and job.get("status") == "done" and path.is_file():
            yield {"id": directory.name, "label": 1, "source": job.get("model") or "sadtalker", "path": path}


parser = argparse.ArgumentParser()
parser.add_argument("--data", type=Path, default=Path("/opt/media-app/local-media/data"))
parser.add_argument("--detector", type=Path, default=Path("/opt/media-app/local-media/detect.py"))
parser.add_argument("--models", type=Path, default=Path("/opt/media-models/DeepfakeBench"))
parser.add_argument("--python", type=Path, default=Path("/opt/media-models/DeepfakeBench/.venv/bin/python"))
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--cache", type=Path)
args = parser.parse_args()

cache = args.cache or args.output.parent / "calibration-cache"
cache.mkdir(parents=True, exist_ok=True)
rows = []
for index, item in enumerate(generated_videos(args.data), 1):
    report_path = cache / f"{item['id']}.json"
    if not report_path.is_file():
        print(f"CALIBRATION {index} {item['id']} {item['source']}", flush=True)
        subprocess.run([
            str(args.python), str(args.detector), str(item["path"]),
            str(args.models), str(report_path),
        ], check=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows.append({
        **{key: item[key] for key in ("id", "label", "source")},
        "scores": {method["id"]: method.get("ai_probability") for method in report["methods"]},
    })
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"CALIBRATION_COMPLETE {len(rows)}", flush=True)
