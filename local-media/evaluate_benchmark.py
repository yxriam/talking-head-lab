"""Evaluate identity, geometry, temporal stability, sharpness and prepare SyncNet inputs."""

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from scipy.signal import savgol_filter


MODELS = ("sadtalker", "echomimic_v1", "joyvasa", "echomimic_v3_flash")


def largest_face(app, frame):
    faces = app.get(frame)
    if not faces:
        return None
    return max(faces, key=lambda face: np.prod(face.bbox[2:] - face.bbox[:2]))


def smooth(values):
    values = np.asarray(values, dtype=np.float32)
    if len(values) >= 5:
        return savgol_filter(values, 5, 2, axis=0, mode="interp")
    return values


def crop_face(frame, bbox, size=224):
    x1, y1, x2, y2 = bbox
    width, height = x2 - x1, y2 - y1
    side = max(width, height) * 1.65
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2 + height * 0.10
    left, top = int(round(cx - side / 2)), int(round(cy - side / 2))
    right, bottom = int(round(cx + side / 2)), int(round(cy + side / 2))
    pad_left, pad_top = max(0, -left), max(0, -top)
    pad_right, pad_bottom = max(0, right - frame.shape[1]), max(0, bottom - frame.shape[0])
    if any((pad_left, pad_top, pad_right, pad_bottom)):
        frame = cv2.copyMakeBorder(frame, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_REFLECT_101)
        left, right = left + pad_left, right + pad_left
        top, bottom = top + pad_top, bottom + pad_top
    return cv2.resize(frame[top:bottom, left:right], (size, size), interpolation=cv2.INTER_LANCZOS4)


def aligned_keypoints(kps):
    eyes = kps[:2]
    center = eyes.mean(axis=0)
    delta = eyes[1] - eyes[0]
    scale = max(float(np.linalg.norm(delta)), 1e-6)
    angle = -math.atan2(float(delta[1]), float(delta[0]))
    rotation = np.array([[math.cos(angle), -math.sin(angle)],
                         [math.sin(angle), math.cos(angle)]], dtype=np.float32)
    return ((kps - center) @ rotation.T) / scale


def evaluate_model(app, reference_embedding, work):
    video = work / "output.mp4"
    capture = cv2.VideoCapture(str(video))
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 25)
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    if not frames:
        raise RuntimeError(f"No video frames in {video}")

    stride = max(1, int(os.environ.get("EVAL_FRAME_STRIDE", "1")))
    sample_indices = list(range(0, len(frames), stride))
    if sample_indices[-1] != len(frames) - 1:
        sample_indices.append(len(frames) - 1)
    detected = [None] * len(frames)
    for index in sample_indices:
        detected[index] = largest_face(app, frames[index])
    valid = [(index, detected[index]) for index in sample_indices if detected[index] is not None]
    if not valid:
        raise RuntimeError(f"No faces detected in {video}")

    similarities, sharpness, black_ratios = [], [], []
    normalized_kps, geometry, rolls, yaw_proxy = [], [], [], []
    lip_aperture, lip_width, lip_asymmetry = [], [], []
    boxes = np.full((len(frames), 4), np.nan, dtype=np.float32)
    for index, frame in enumerate(frames):
        face = detected[index]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        black_ratios.append(float(np.mean(gray < 8)))
        if face is None:
            continue
        boxes[index] = face.bbox
        similarities.append(float(np.dot(reference_embedding, face.normed_embedding)))
        x1, y1, x2, y2 = np.clip(face.bbox.astype(int), [0, 0, 0, 0],
                                  [frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
        face_gray = gray[y1:y2, x1:x2]
        sharpness.append(float(cv2.Laplacian(face_gray, cv2.CV_64F).var()) if face_gray.size else 0.0)
        kps = face.kps.astype(np.float32)
        norm = aligned_keypoints(kps)
        normalized_kps.append(norm)
        eye_distance = max(float(np.linalg.norm(kps[1] - kps[0])), 1e-6)
        eye_mid, mouth_mid = kps[:2].mean(axis=0), kps[3:5].mean(axis=0)
        geometry.append([
            float(np.linalg.norm(kps[4] - kps[3]) / eye_distance),
            float((mouth_mid[1] - eye_mid[1]) / eye_distance),
            float((kps[2, 1] - eye_mid[1]) / eye_distance),
        ])
        rolls.append(math.degrees(math.atan2(float(kps[1, 1] - kps[0, 1]),
                                             float(kps[1, 0] - kps[0, 0]))))
        yaw_proxy.append(float((kps[2, 0] - eye_mid[0]) / eye_distance))
        landmarks = face.landmark_3d_68[:, :2].astype(np.float32)
        left_eye = landmarks[36:42].mean(axis=0)
        right_eye = landmarks[42:48].mean(axis=0)
        detailed_eye_distance = max(float(np.linalg.norm(right_eye - left_eye)), 1e-6)
        inner_opening = np.mean([
            np.linalg.norm(landmarks[61] - landmarks[67]),
            np.linalg.norm(landmarks[62] - landmarks[66]),
            np.linalg.norm(landmarks[63] - landmarks[65]),
        ]) / detailed_eye_distance
        left_opening = float(np.linalg.norm(landmarks[61] - landmarks[67]) / detailed_eye_distance)
        right_opening = float(np.linalg.norm(landmarks[63] - landmarks[65]) / detailed_eye_distance)
        lip_aperture.append(float(inner_opening))
        lip_width.append(float(np.linalg.norm(landmarks[54] - landmarks[48]) / detailed_eye_distance))
        lip_asymmetry.append(abs(left_opening - right_opening))

    for column in range(4):
        good = np.flatnonzero(~np.isnan(boxes[:, column]))
        boxes[:, column] = np.interp(np.arange(len(boxes)), good, boxes[good, column])
    boxes = smooth(boxes)

    raw_video = work / "sync-face-noaudio.mp4"
    writer = cv2.VideoWriter(str(raw_video), cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (224, 224))
    target_count = max(6, round((len(frames) / fps) * 25))
    for out_index in range(target_count):
        source_index = min(len(frames) - 1, round(out_index * fps / 25))
        writer.write(crop_face(frames[source_index], boxes[source_index]))
    writer.release()
    sync_video = work / "sync-input.mp4"
    subprocess.run([
        "ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(raw_video), "-i", str(video),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(sync_video)
    ], check=True)

    similarities = np.asarray(similarities)
    norm = np.asarray(normalized_kps)
    second_difference = np.diff(norm, n=2, axis=0)
    jitter = float(np.mean(np.linalg.norm(second_difference, axis=2))) if len(norm) >= 3 else 0.0
    geometry = np.asarray(geometry)
    median = np.median(geometry, axis=0)
    mad = np.median(np.abs(geometry - median), axis=0)
    tolerance = np.maximum(4 * mad, np.array([0.10, 0.10, 0.08]))
    outliers = np.any(np.abs(geometry - median) > tolerance, axis=1)
    lip_aperture = np.asarray(lip_aperture)
    lip_width = np.asarray(lip_width)
    lip_second_difference = np.diff(lip_aperture, n=2)

    performance = json.loads((work / "performance.json").read_text())
    try:
        duration = float(performance["output"]["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        duration = len(frames) / fps
    metrics = {
        "frames": len(frames),
        "evaluated_frames": len(sample_indices),
        "face_detection_rate": round(len(valid) / len(sample_indices), 4),
        "identity_mean": round(float(np.mean(similarities)), 4),
        "identity_p05": round(float(np.percentile(similarities, 5)), 4),
        "identity_min": round(float(np.min(similarities)), 4),
        "identity_std": round(float(np.std(similarities)), 4),
        "geometry_outlier_rate": round(float(np.mean(outliers)), 4),
        "landmark_jitter": round(jitter, 4),
        "lip_aperture_range": round(float(np.ptp(lip_aperture)), 4),
        "lip_motion_jitter": round(float(np.mean(np.abs(lip_second_difference))), 4),
        "lip_width_cv": round(float(np.std(lip_width) / max(np.mean(lip_width), 1e-6)), 4),
        "lip_asymmetry_mean": round(float(np.mean(lip_asymmetry)), 4),
        "roll_range_deg": round(float(np.ptp(rolls)), 2),
        "yaw_proxy_range": round(float(np.ptp(yaw_proxy)), 4),
        "face_sharpness": round(float(np.mean(sharpness)), 1),
        "black_pixel_ratio": round(float(np.mean(black_ratios)), 4),
        "rtf": round(float(performance["wall_seconds"]) / duration, 2),
    }
    (work / "visual-metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(work.name, json.dumps(metrics, ensure_ascii=False))
    return metrics


def main(run_root: Path, model_root: Path):
    app = FaceAnalysis(name="antelopev2", root=str(model_root / "InstantID"),
                       providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    reference = cv2.imread(str(run_root / "sadtalker/input.png"))
    reference_face = largest_face(app, reference)
    if reference_face is None:
        raise RuntimeError("No face in benchmark reference")
    summary = {}
    for model in MODELS:
        summary[model] = evaluate_model(app, reference_face.normed_embedding, run_root / model)
    (run_root / "visual-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
