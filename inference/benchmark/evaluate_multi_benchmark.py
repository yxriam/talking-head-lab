"""Run frame-level identity, motion and stability metrics for a multi-case benchmark."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
from insightface.app import FaceAnalysis

from evaluate_benchmark import evaluate_model, largest_face


MODELS = ("sadtalker", "echomimic_v1", "joyvasa", "echomimic_v3_flash")


def main(root: Path, model_root: Path, selected=MODELS):
    app = FaceAnalysis(name="antelopev2", root=str(model_root / "InstantID"), providers=["CPUExecutionProvider"])
    # Outputs are 256–512 px portraits; 320 px detection is sufficient and
    # keeps the CPU-only multi-sample evaluation practical.
    app.prepare(ctx_id=-1, det_size=(320, 320))
    previous = []
    result_path = root / "visual-results.json"
    if result_path.exists() and tuple(selected) != MODELS:
        previous = [
            row for row in json.loads(result_path.read_text(encoding="utf-8"))
            if row.get("model") not in selected
        ]
    rows = list(previous)
    for case in sorted((root / "cases").iterdir()):
        if not case.is_dir():
            continue
        reference = cv2.imread(str(case / "input.png"))
        reference_face = largest_face(app, reference)
        if reference_face is None:
            rows.append({"case_id": case.name, "model": None, "error": "reference face missing"})
            continue
        for model in selected:
            work = case / model
            if not (work / "output.mp4").exists():
                rows.append({"case_id": case.name, "model": model, "error": "generation failed"})
                continue
            try:
                metrics = evaluate_model(app, reference_face.normed_embedding, work)
                rows.append({"case_id": case.name, "model": model, **metrics})
            except Exception as exc:
                rows.append({"case_id": case.name, "model": model, "error": str(exc)})
        result_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "errors": sum('error' in r for r in rows)}))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), tuple(sys.argv[3:]) or MODELS)
