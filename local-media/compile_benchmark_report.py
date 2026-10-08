"""Merge benchmark artifacts into JSON, CSV, Markdown, and a comparison sheet."""

import csv
import json
import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont


MODELS = {
    "sadtalker": "SadTalker",
    "echomimic_v1": "EchoMimic V1",
    "joyvasa": "JoyVASA",
    "echomimic_v3_flash": "EchoMimic V3 Flash",
}


def main(root: Path):
    sync = json.loads((root / "syncnet-summary.json").read_text())
    rows = []
    for key, label in MODELS.items():
        work = root / key
        performance = json.loads((work / "performance.json").read_text())
        visual = json.loads((work / "visual-metrics.json").read_text())
        stream = next(item for item in performance["output"]["streams"] if item["codec_type"] == "video")
        row = {
            "model": label,
            "wall_seconds": performance["wall_seconds"],
            "rtf": visual["rtf"],
            "peak_gpu_mb": performance["peak_gpu_memory_mb"],
            "max_rss_mb": performance["max_rss_mb"],
            "resolution": f'{stream["width"]}x{stream["height"]}',
            "fps": stream["r_frame_rate"],
            "identity_mean": visual["identity_mean"],
            "identity_p05": visual["identity_p05"],
            "identity_min": visual["identity_min"],
            "identity_std": visual["identity_std"],
            "lse_d": sync[key]["lse_d"],
            "lse_c": sync[key]["lse_c"],
            "av_offset_frames": sync[key]["av_offset_frames"],
            "lip_aperture_range": visual["lip_aperture_range"],
            "lip_motion_jitter": visual["lip_motion_jitter"],
            "lip_width_cv": visual["lip_width_cv"],
            "lip_asymmetry_mean": visual["lip_asymmetry_mean"],
            "landmark_jitter": visual["landmark_jitter"],
            "geometry_outlier_rate": visual["geometry_outlier_rate"],
            "face_sharpness": visual["face_sharpness"],
            "face_detection_rate": visual["face_detection_rate"],
        }
        rows.append(row)

    (root / "benchmark-summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    with (root / "benchmark-summary.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# 本地人像视频模型同输入基准",
        "",
        "固定输入：同一张 768×768 原像素人物/新背景肖像、同一段约 2.4 秒单人语音。",
        "模型阶段单独计时，不包含共享的 Qwen 场景分类和 SDXL/U2Net 背景处理。",
        "",
        "## 速度与资源",
        "",
        "| 模型 | 时间(s) | RTF↓ | 峰值显存(MB)↓ | 最大RSS(MB)↓ | 输出 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(f'| {row["model"]} | {row["wall_seconds"]:.1f} | {row["rtf"]:.2f} | '
                     f'{row["peak_gpu_mb"]} | {row["max_rss_mb"]:.1f} | {row["resolution"]} {row["fps"]} |')
    lines += [
        "",
        "## 身份与唇音同步",
        "",
        "| 模型 | 身份均值↑ | P05↑ | 最低↑ | LSE-D↓ | LSE-C↑ | 偏移帧→0 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(f'| {row["model"]} | {row["identity_mean"]:.4f} | {row["identity_p05"]:.4f} | '
                     f'{row["identity_min"]:.4f} | {row["lse_d"]:.3f} | {row["lse_c"]:.3f} | '
                     f'{row["av_offset_frames"]} |')
    lines += [
        "",
        "## 嘴形与时间稳定性",
        "",
        "| 模型 | 开合范围 | 嘴部抖动↓ | 嘴宽CV↓ | 不对称↓ | 全脸关键点抖动↓ | 几何异常率↓ | 清晰度↑ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(f'| {row["model"]} | {row["lip_aperture_range"]:.4f} | '
                     f'{row["lip_motion_jitter"]:.4f} | {row["lip_width_cv"]:.4f} | '
                     f'{row["lip_asymmetry_mean"]:.4f} | {row["landmark_jitter"]:.4f} | '
                     f'{row["geometry_outlier_rate"]:.1%} | {row["face_sharpness"]:.1f} |')
    lines += [
        "",
        "## 结论",
        "",
        "- 身份保持与本样本的音画同步：SadTalker 最好。",
        "- 速度与动作表现：JoyVASA 最快且嘴部开合最大，但身份漂移和嘴部抖动也更明显。",
        "- EchoMimic V1 身份保持较好，但速度、清晰度和 SyncNet 置信度没有优势。",
        "- EchoMimic V3 Flash 清晰度最高，但本样本速度最慢、身份保持最低，且 SyncNet 偏移达到 -13 帧。",
        "",
        "LSE-D/LSE-C 衡量音画同步，不是有真实口型标注的‘唇形准确率’。嘴形自然度由68点开合、抖动、宽度变化与不对称指标补充。单一照片/音频只能用于受控对比，不能代表跨人物总体准确率。",
    ]
    (root / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    samples = (0.15, 0.4, 0.65, 0.9)
    cell = 256
    label_width = 190
    sheet = Image.new("RGB", (label_width + cell * len(samples), cell * len(rows)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row_index, (key, label) in enumerate(MODELS.items()):
        cap = cv2.VideoCapture(str(root / key / "output.mp4"))
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        draw.text((12, row_index * cell + 16), label, fill="black", font=font)
        for column, fraction in enumerate(samples):
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, round((count - 1) * fraction)))
            ok, frame = cap.read()
            if not ok:
                continue
            height, width = frame.shape[:2]
            scale = cell / min(width, height)
            resized = cv2.resize(frame, (round(width * scale), round(height * scale)))
            y = max(0, (resized.shape[0] - cell) // 2)
            x = max(0, (resized.shape[1] - cell) // 2)
            crop = cv2.cvtColor(resized[y:y + cell, x:x + cell], cv2.COLOR_BGR2RGB)
            sheet.paste(Image.fromarray(crop), (label_width + column * cell, row_index * cell))
        cap.release()
    sheet.save(root / "comparison-sheet.jpg", quality=92)
    print(root / "REPORT.md")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
