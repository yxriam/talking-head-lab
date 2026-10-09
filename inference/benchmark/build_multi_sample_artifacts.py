"""Aggregate a multi-sample benchmark and build screenshot/video review artifacts."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont


MODELS = ("sadtalker", "echomimic_v1", "joyvasa", "echomimic_v3_flash")
LABELS = {
    "sadtalker": "SadTalker",
    "echomimic_v1": "EchoMimic V1",
    "joyvasa": "JoyVASA",
    "echomimic_v3_flash": "EchoMimic V3 Flash",
}


def mean_std(values):
    values = [float(v) for v in values if v is not None]
    if not values:
        return None, None
    return round(statistics.mean(values), 4), round(statistics.pstdev(values), 4)


def video_frame(path: Path, fraction=0.5):
    cap = cv2.VideoCapture(str(path))
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if count > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, min(count - 1, int(count * fraction))))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def fit(image: Image.Image, size):
    image = image.copy().convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def font(size=22):
    for candidate in ("/mnt/c/Windows/Fonts/msyh.ttc", "/mnt/c/Windows/Fonts/arial.ttf"):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def build_contact(root: Path, manifest, asset_dir: Path):
    rows = [row for row in manifest if row["audio_id"] == "a01"]
    headers = ["输入照片"] + [LABELS[m] for m in MODELS]
    cell_w, cell_h, label_h = 220, 220, 42
    for page, subset in enumerate((rows[:4], rows[4:]), 1):
        canvas = Image.new("RGB", (cell_w * len(headers), label_h + cell_h * len(subset)), "white")
        draw = ImageDraw.Draw(canvas)
        for col, title in enumerate(headers):
            draw.rectangle((col * cell_w, 0, (col + 1) * cell_w, label_h), fill="#17324d")
            draw.text((col * cell_w + 10, 8), title, font=font(20), fill="white")
        for row_i, item in enumerate(subset):
            case = root / "cases" / item["case_id"]
            images = [Image.open(case / "input.png")]
            for model in MODELS:
                path = case / model / "output.mp4"
                images.append(video_frame(path) if path.exists() else None)
            for col, image in enumerate(images):
                x, y = col * cell_w, label_h + row_i * cell_h
                draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline="#d9e2e7")
                if image is None:
                    draw.text((x + 55, y + 92), "运行失败", font=font(22), fill="#b65050")
                else:
                    canvas.paste(fit(image, (cell_w - 2, cell_h - 2)), (x + 1, y + 1))
                draw.rectangle((x + 5, y + 5, x + 78, y + 33), fill="white")
                draw.text((x + 10, y + 7), item["case_id"], font=font(16), fill="#17324d")
        out = asset_dir / f"multi-sample-contact-{page}.jpg"
        canvas.save(out, quality=92)


def build_gallery(root: Path, manifest, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in manifest:
        cards = []
        for model in MODELS:
            video = root / "cases" / item["case_id"] / model / "output.mp4"
            if video.exists():
                rel = video.relative_to(root).as_posix()
                cards.append(f'<div class="card"><h3>{LABELS[model]}</h3><video controls preload="metadata" src="../../benchmark-results/{root.name}/{rel}"></video></div>')
            else:
                cards.append(f'<div class="card failed"><h3>{LABELS[model]}</h3><p>运行失败</p></div>')
        rows.append(f'<section><h2>{item["case_id"]} · {item["photo_source"]} · {item["audio_source"]}</h2><div class="grid">{"".join(cards)}</div></section>')
    html = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>多样本效果视频</title>
<style>body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:24px;color:#17324d;background:#f4f7f8}}section{{background:white;padding:18px;margin:0 0 20px;border-radius:12px}}h1{{margin-bottom:4px}}h2{{font-size:17px}}h3{{font-size:14px;margin:0 0 8px}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(220px,1fr));gap:14px}}video{{width:100%;max-height:340px;background:#111}}.card{{border:1px solid #d9e2e7;padding:10px;border-radius:9px}}.failed{{display:grid;place-content:center;min-height:200px;color:#b65050}}@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}</style>
<h1>音频驱动人像多样本效果视频</h1><p>14 组相同输入条件下的逐模型结果；失败项同样保留。</p>{''.join(rows)}</html>'''
    (out_dir / "video-gallery.html").write_text(html, encoding="utf-8")


def aggregate(root: Path, manifest):
    visuals_path = root / "visual-results.json"
    visuals = json.loads(visuals_path.read_text(encoding="utf-8")) if visuals_path.exists() else []
    visual_index = {(x["case_id"], x["model"]): x for x in visuals if x.get("model") and "error" not in x}
    metrics = ("identity_mean", "identity_p05", "face_detection_rate", "landmark_jitter", "lip_aperture_range", "face_sharpness")
    result = {"sample_count": len(manifest), "models": {}}
    for model in MODELS:
        perf = []
        for item in manifest:
            path = root / "cases" / item["case_id"] / model / "performance.json"
            if path.exists():
                perf.append(json.loads(path.read_text(encoding="utf-8")))
        successes = [p for p in perf if p.get("exit_code") == 0]
        isolated = [p for p in successes if p.get("execution_mode") != "warm_batch_after_single_model_load"]
        warm_batch = [p for p in successes if p.get("execution_mode") == "warm_batch_after_single_model_load"]
        comparable = isolated or successes
        sync_rows = []
        for item in manifest:
            sync_file = root / "cases" / item["case_id"] / model / "syncnet-metrics.json"
            if sync_file.exists():
                sync_rows.append(json.loads(sync_file.read_text(encoding="utf-8")))
        row = {"attempted": len(perf), "successes": len(successes), "success_rate": round(len(successes) / len(perf), 4) if perf else None}
        for key in ("wall_seconds", "max_rss_mb", "peak_gpu_memory_mb"):
            row[key + "_mean"], row[key + "_std"] = mean_std([p.get(key) for p in comparable])
        row["warm_batch_samples"] = len(warm_batch)
        row["warm_batch_wall_seconds_mean"], row["warm_batch_wall_seconds_std"] = mean_std(
            [p.get("wall_seconds") for p in warm_batch]
        )
        for key in metrics:
            row[key + "_mean"], row[key + "_std"] = mean_std([visual_index.get((i["case_id"], model), {}).get(key) for i in manifest])
        for key in ("lse_d", "lse_c", "av_offset_frames"):
            row[key + "_mean"], row[key + "_std"] = mean_std([x.get(key) for x in sync_rows])
        result["models"][model] = row
    (root / "aggregate-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(root: Path, asset_dir: Path, gallery_dir: Path):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    asset_dir.mkdir(parents=True, exist_ok=True)
    build_contact(root, manifest, asset_dir)
    build_gallery(root, manifest, gallery_dir)
    print(json.dumps(aggregate(root, manifest), ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
