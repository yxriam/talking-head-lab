"""Re-evaluate cached model scores without running GPU inference again."""

import json
import hashlib
from pathlib import Path

from detect import learned_result, summarize_learned, target_indices


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def temporal_decision(path):
    import cv2
    import numpy as np
    capture = cv2.VideoCapture(str(path))
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    indices, _ = target_indices(count, fps)
    frames = []
    index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if index in indices:
            gray = cv2.cvtColor(cv2.resize(frame, (256, 256)), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
            frames.append(gray)
        index += 1
    capture.release()
    median = float(np.median([np.abs(a - b).mean() for a, b in zip(frames, frames[1:])]))
    return "fail" if median < 0.0135 else "pass", median


root = Path(__file__).parent
rows = list({row["sha256"]: row for row in json.loads((root / "calibration-labeled.json").read_text(encoding="utf-8"))}.values())
paths = {}
for folder in (Path("/mnt/d/project/data/real"), Path("/mnt/d/project/data/fake")):
    for path in folder.iterdir():
        if path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
            paths.setdefault(sha256(path), path)
correct = 0
for row in rows:
    report = json.loads((root / "calibration-labeled-cache" / f"{row['sha256']}.json").read_text(encoding="utf-8"))
    methods = []
    for old in report["methods"]:
        values = [frame["score"] for frame in old.get("frames", [])]
        if not values:
            median = old.get("metrics", {}).get("采样中位数")
            if median is None:
                methods.append(old)
                continue
            values = [median]
        methods.append(learned_result(
            old["id"], old["name"], values, old.get("principle", ""),
            old.get("paper", ""), "video",
        ))
    temporal, value = temporal_decision(paths[row["sha256"]])
    methods.append({"id":"temporal_static", "name":"照片驱动时序静态性", "status":"done",
                    "decision":temporal, "ai_probability":0.9 if temporal == "fail" else 0.1,
                    "metrics":{"相邻画面变化中位数":value}})
    verdict = summarize_learned(methods)["verdict"]
    expected = "真实拍摄倾向" if row["label"] == "real" else "AI 生成倾向"
    correct += verdict == expected
    if verdict != expected:
        print("MISCLASSIFIED", row["label"], row["name"], verdict,
              [(item["id"], item.get("decision"), item.get("ai_probability")) for item in methods])
print(f"RESULT unique={len(rows)} correct={correct} accuracy={correct / len(rows):.4f}")
