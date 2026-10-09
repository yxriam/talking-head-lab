"""Run detector regression on user-labelled real and fake folders.

Folder names are used only to evaluate thresholds offline. The detector never
receives the label or path category as a prediction input.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def videos(folder):
    return sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES)


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--real", type=Path, required=True)
parser.add_argument("--fake", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--cache", type=Path, required=True)
parser.add_argument("--detector", type=Path, default=Path("/opt/media-app/local-media/detect.py"))
parser.add_argument("--models", type=Path, default=Path("/opt/media-models/DeepfakeBench"))
parser.add_argument("--python", type=Path, default=Path("/opt/media-models/DeepfakeBench/.venv/bin/python"))
args = parser.parse_args()
args.cache.mkdir(parents=True, exist_ok=True)

rows = []
items = [(path, "real") for path in videos(args.real)] + [(path, "fake") for path in videos(args.fake)]
for index, (path, label) in enumerate(items, 1):
    sha256 = digest(path)
    report_path = args.cache / f"{sha256}.json"
    if not report_path.is_file():
        print(f"CALIBRATION {index}/{len(items)} {label} {path.name}", flush=True)
        subprocess.run([str(args.python), str(args.detector), str(path), str(args.models), str(report_path)], check=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows.append({
        "name": path.name,
        "sha256": sha256,
        "label": label,
        "verdict": report["verdict"],
        "methods": {
            method["id"]: {
                "decision": method.get("decision"),
                "ai_probability": method.get("ai_probability"),
                "metrics": method.get("metrics", {}),
            }
            for method in report["methods"]
        },
    })
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

unique = {row["sha256"]: row for row in rows}.values()
correct = sum(
    (row["label"] == "real" and row["verdict"] == "真实拍摄倾向")
    or (row["label"] == "fake" and row["verdict"] == "AI 生成倾向")
    for row in unique
)
print(f"CALIBRATION_COMPLETE unique={len(list(unique))} correct={correct}", flush=True)
