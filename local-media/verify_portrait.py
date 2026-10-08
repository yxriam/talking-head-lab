"""Measure face identity similarity and output dimensions for portrait QA."""

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from PIL import Image


def largest_face(app: FaceAnalysis, path: Path):
    image = cv2.imread(str(path))
    faces = app.get(image)
    if not faces:
        raise ValueError(f"No face detected in {path}")
    return max(faces, key=lambda face: np.prod(face.bbox[2:] - face.bbox[:2]))


def main(source: Path, generated: Path, model_root: Path):
    app = FaceAnalysis(
        name="antelopev2",
        root=str(model_root / "InstantID"),
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))
    source_face = largest_face(app, source)
    generated_face = largest_face(app, generated)
    similarity = float(
        np.dot(source_face.normed_embedding, generated_face.normed_embedding)
    )
    with Image.open(generated) as image:
        size = image.size
    print(json.dumps({"cosine_similarity": round(similarity, 4), "size": size}))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
