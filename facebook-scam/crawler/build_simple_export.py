from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\desktop\exam\cv\facebook-scam\data\accounts")
OUT = Path(r"D:\desktop\exam\cv\facebook-scam\data\final_accounts")


MEDIA_GROUPS = {
    "image": [
        "person_visual_candidates",
        "relationship_visual_context",
        "content_visual_context",
    ],
    "video": [
        "person_video_candidates",
        "scene_videos_not_face_or_voice_candidates",
    ],
    "audio": [
        "voice_candidate_tracks_needs_asr",
    ],
}


def ensure_inside(path: Path, base: Path) -> None:
    resolved = path.resolve()
    base_resolved = base.resolve()
    if base_resolved not in (resolved, *resolved.parents):
        raise ValueError(f"path escapes expected root: {path}")


def clean_output() -> None:
    ensure_inside(OUT, ROOT.parent)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)


def copy_unique(src: Path, dst_dir: Path) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.exists():
        dst = dst_dir / f"{src.stem}_{abs(hash(str(src))) & 0xffff:x}{src.suffix}"
    shutil.copy2(src, dst)
    return dst


def copy_text(account_dir: Path, out_dir: Path) -> list[dict]:
    text_dir = out_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    sources = [
        (account_dir / "content" / "content.txt", "visible_text.txt", "plain_visible_text"),
        (account_dir / "content" / "content.json", "visible_text.json", "structured_visible_text"),
        (account_dir / "content" / "content.csv", "visible_text.csv", "tabular_visible_text"),
    ]
    raw_dir = account_dir / "raw"
    if raw_dir.exists():
        raw_texts = sorted(raw_dir.glob("visible_text_*.txt"))
        if raw_texts:
            merged = text_dir / "raw_visible_text_snapshots.txt"
            with merged.open("w", encoding="utf-8", newline="\n") as handle:
                for raw in raw_texts:
                    handle.write(f"\n\n===== {raw.name} =====\n")
                    handle.write(raw.read_text(encoding="utf-8", errors="replace"))
            copied.append({"kind": "raw_visible_text_snapshots", "path": str(merged)})
    for src, name, kind in sources:
        if src.exists():
            dst = text_dir / name
            shutil.copy2(src, dst)
            copied.append({"kind": kind, "path": str(dst)})
    return copied


def collect_media(account_report: dict, account_dir: Path, out_dir: Path) -> list[dict]:
    rows = []
    kept = account_report.get("kept", {})
    for media_type, categories in MEDIA_GROUPS.items():
        dst_dir = out_dir / media_type
        dst_dir.mkdir(parents=True, exist_ok=True)
        for category in categories:
            for item in kept.get(category, []):
                rel_path = item.get("path")
                if not rel_path:
                    continue
                src = account_dir / rel_path
                if not src.exists():
                    rows.append(
                        {
                            "type": media_type,
                            "category": category,
                            "source": str(src),
                            "output": "",
                            "status": "missing_source",
                        }
                    )
                    continue
                dst = copy_unique(src, dst_dir)
                rows.append(
                    {
                        "type": media_type,
                        "category": category,
                        "source": str(src),
                        "output": str(dst),
                        "status": "copied",
                    }
                )
    return rows


def write_index(out_dir: Path, account_slug: str, media_rows: list[dict], text_rows: list[dict]) -> None:
    index = {
        "account_slug": account_slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "layout": {
            "image": "curated usable images and relationship/content context images",
            "video": "curated usable original Facebook videos",
            "audio": "clean voice-candidate audio tracks only; background/unmatched/legacy recordings excluded",
            "text": "original visible text exports",
        },
        "media": media_rows,
        "text": text_rows,
    }
    (out_dir / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out_dir / "index.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["type", "category", "source", "output", "status"])
        writer.writeheader()
        writer.writerows(media_rows)


def main() -> None:
    report_path = ROOT / "curation_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    clean_output()
    summary_rows = []
    for account_report in report["accounts"]:
        account_slug = account_report["account_slug"]
        account_dir = Path(account_report["account_dir"])
        ensure_inside(account_dir, ROOT)
        out_dir = OUT / account_slug
        for name in ("image", "video", "audio", "text"):
            (out_dir / name).mkdir(parents=True, exist_ok=True)
        media_rows = collect_media(account_report, account_dir, out_dir)
        text_rows = copy_text(account_dir, out_dir)
        write_index(out_dir, account_slug, media_rows, text_rows)
        summary_rows.append(
            {
                "account_slug": account_slug,
                "image_count": sum(1 for row in media_rows if row["type"] == "image" and row["status"] == "copied"),
                "video_count": sum(1 for row in media_rows if row["type"] == "video" and row["status"] == "copied"),
                "audio_count": sum(1 for row in media_rows if row["type"] == "audio" and row["status"] == "copied"),
                "text_files": len(text_rows),
                "account_dir": str(out_dir),
            }
        )
    (OUT / "summary.json").write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")
    with (OUT / "summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["account_slug", "image_count", "video_count", "audio_count", "text_files", "account_dir"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(OUT)


if __name__ == "__main__":
    main()
