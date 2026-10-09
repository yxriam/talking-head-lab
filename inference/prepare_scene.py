"""Generate a new background while preserving the person's original pixels."""

import hashlib
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-media")

import cv2
import numpy as np
import torch
from diffusers import EulerDiscreteScheduler, StableDiffusionXLPipeline
from insightface.app import FaceAnalysis
from PIL import Image, ImageFilter


def portrait_crop(image: Image.Image, bbox: np.ndarray, target: tuple[int, int]) -> Image.Image:
    """Crop around the detected face without changing the person's geometry."""
    width, height = image.size
    target_width, target_height = target
    ratio = target_width / target_height
    face_width = float(bbox[2] - bbox[0])
    face_height = float(bbox[3] - bbox[1])

    crop_width = max(face_width / 0.28, face_height * ratio / 0.30)
    crop_height = crop_width / ratio
    if crop_width > width:
        crop_width = float(width)
        crop_height = crop_width / ratio
    if crop_height > height:
        crop_height = float(height)
        crop_width = crop_height * ratio

    face_x = float((bbox[0] + bbox[2]) / 2)
    face_y = float((bbox[1] + bbox[3]) / 2)
    left = min(max(face_x - crop_width / 2, 0), width - crop_width)
    top = min(max(face_y - crop_height * 0.30, 0), height - crop_height)
    box = (round(left), round(top), round(left + crop_width), round(top + crop_height))
    return image.crop(box).resize(target, Image.Resampling.LANCZOS)


def main(source: Path, output: Path, model_root: Path, scene: str, square: bool):
    instant = model_root / "InstantID"
    weights = instant / "weights"
    target = (768, 768 if square else 1024)
    image = Image.open(source).convert("RGB")

    face_app = FaceAnalysis(name="antelopev2", root=str(instant), providers=["CPUExecutionProvider"])
    face_app.prepare(ctx_id=-1, det_size=(640, 640))
    faces = face_app.get(cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR))
    if not faces:
        raise ValueError("未在原图中检测到人脸")
    face = max(faces, key=lambda item: (item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]))
    foreground = portrait_crop(image, face.bbox, target)

    # Only the empty scene is generated. The person's face and body are not redrawn.
    pipe = StableDiffusionXLPipeline.from_pretrained(
        weights / "sdxl-base", torch_dtype=torch.float16, variant="fp16", local_files_only=True)
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_tiling()
    seed_material = source.read_bytes() + scene.encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:4], "big")
    background = pipe(
        prompt=("empty interior background plate with no people, photorealistic professional photography, "
                "soft depth of field, open space in the center for a portrait subject, uniform low-detail area behind "
                "the central head-and-shoulders silhouette, no structural edges near the head or shoulders, " + scene),
        negative_prompt=("person, people, human, face, body, silhouette, mannequin, text, watermark, "
                         "distorted architecture, clutter, illustration, painting, low quality, picture frame, sign, "
                         "shelf, window frame, doorway, horizontal line or vertical line crossing the center, object "
                         "touching the subject silhouette"),
        num_inference_steps=30,
        guidance_scale=5.0,
        width=target[0],
        height=target[1],
        generator=torch.Generator(device="cpu").manual_seed(seed),
    ).images[0].filter(ImageFilter.GaussianBlur(0.7))
    del pipe
    torch.cuda.empty_cache()

    os.environ["U2NET_HOME"] = str(weights / "rembg")
    from rembg import new_session, remove

    session = new_session("u2net_human_seg")
    mask_array = remove(np.asarray(foreground), session=session, only_mask=True, post_process_mask=True)
    mask = Image.fromarray(mask_array).convert("L").filter(ImageFilter.GaussianBlur(1.2))
    result = Image.composite(foreground, background, mask)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output, format="PNG")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]),
         Path(sys.argv[4]).read_text(encoding="utf-8").strip(), sys.argv[5] == "square")
