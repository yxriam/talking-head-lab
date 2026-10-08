"""Evaluate one EchoMimic V3 benchmark case for parallel CPU execution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
from insightface.app import FaceAnalysis

from evaluate_benchmark import evaluate_model, largest_face


def main(case: Path, model_root: Path, output: Path) -> None:
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if "error" not in previous:
            print(json.dumps({"case_id": case.name, "status": "already complete"}, ensure_ascii=False))
            return
    app = FaceAnalysis(name="antelopev2", root=str(model_root / "InstantID"), providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(320, 320))
    row = {"case_id": case.name, "model": "echomimic_v3_flash"}
    try:
        reference = cv2.imread(str(case / "input.png"))
        reference_face = largest_face(app, reference)
        if reference_face is None:
            raise RuntimeError("reference face missing")
        work = case / "echomimic_v3_flash"
        if not (work / "output.mp4").exists():
            raise RuntimeError("generation failed")
        row.update(evaluate_model(app, reference_face.normed_embedding, work))
    except Exception as exc:
        row["error"] = str(exc)
    output.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
