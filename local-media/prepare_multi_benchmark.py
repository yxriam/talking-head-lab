"""Prepare fair multi-sample portrait/audio inputs for all local generators."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from PIL import Image, ImageOps


def square_face_crop(image: Image.Image, bbox, size=768):
    """Keep original pixels while normalizing framing around the largest face."""
    image = ImageOps.exif_transpose(image).convert("RGB")
    width, height = image.size
    x1, y1, x2, y2 = map(float, bbox)
    face_w, face_h = x2 - x1, y2 - y1
    side = max(face_w, face_h) * 2.45
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2 + face_h * 0.18
    left, top = cx - side / 2, cy - side / 2
    right, bottom = left + side, top + side
    pad = (max(0, int(-left)), max(0, int(-top)), max(0, int(right-width)), max(0, int(bottom-height)))
    if any(pad):
        arr = np.asarray(image)
        arr = cv2.copyMakeBorder(arr, pad[1], pad[3], pad[0], pad[2], cv2.BORDER_REFLECT_101)
        image = Image.fromarray(arr)
        left, right = left + pad[0], right + pad[0]
        top, bottom = top + pad[1], bottom + pad[1]
    return image.crop((round(left), round(top), round(right), round(bottom))).resize((size, size), Image.Resampling.LANCZOS)


def main(photo_dir: Path, voice_dir: Path, output: Path, model_root: Path):
    output.mkdir(parents=True, exist_ok=True)
    face_app = FaceAnalysis(name="antelopev2", root=str(model_root / "InstantID"), providers=["CPUExecutionProvider"])
    face_app.prepare(ctx_id=-1, det_size=(640, 640))
    photos = sorted(p for p in photo_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    voices = [voice_dir / "4 Rawnsley Tce.m4a", voice_dir / "ray_video_vbcable.wav"]
    for voice in voices:
        if not voice.exists():
            raise FileNotFoundError(voice)

    prepared_photos = []
    for index, source in enumerate(photos, 1):
        image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
        frame = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        faces = face_app.get(frame)
        if not faces:
            print(f"SKIP no face: {source}", flush=True)
            continue
        face = max(faces, key=lambda f: float((f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1])))
        target = output / "portraits" / f"p{index:02d}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        square_face_crop(image, face.bbox).save(target)
        prepared_photos.append((f"p{index:02d}", source.name, target))

    prepared_audio = []
    for index, source in enumerate(voices, 1):
        target = output / "audio" / f"a{index:02d}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(source), "-t", "2.4",
                        "-ac", "1", "-ar", "16000", "-af", "loudnorm=I=-20:TP=-2:LRA=7", str(target)], check=True)
        prepared_audio.append((f"a{index:02d}", source.name, target))

    manifest = []
    for photo_id, photo_source, photo in prepared_photos:
        for audio_id, audio_source, audio in prepared_audio:
            case_id = f"{photo_id}_{audio_id}"
            case = output / "cases" / case_id
            case.mkdir(parents=True, exist_ok=True)
            (case / "input.png").write_bytes(photo.read_bytes())
            (case / "input.wav").write_bytes(audio.read_bytes())
            manifest.append({"case_id": case_id, "photo_id": photo_id, "audio_id": audio_id,
                             "photo_source": photo_source, "audio_source": audio_source})
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"photos": len(prepared_photos), "audios": len(prepared_audio), "cases": len(manifest)}, ensure_ascii=False))


if __name__ == "__main__":
    main(*(Path(x) for x in sys.argv[1:5]))
