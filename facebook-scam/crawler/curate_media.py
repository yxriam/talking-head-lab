from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\desktop\exam\cv\facebook-scam\data\accounts")
FFPROBE = Path(r"D:\documents\UC\facebook\tools\ffmpeg_extract\ffmpeg-9.0-essentials_build\bin\ffprobe.exe")


IMAGE_DECISIONS = {
    "01_ray_hunt": {
        "person_visual_candidates": [
            "original_media/images/0003_461939093_3052432368233346_7498247809982692129_n.jpg",
            "original_media/images/0004_514620660_10238630792254422_420361085077167201_n.jpg",
            "original_media/images/0014_468324930_10235972170670544_5699329227933363604_n.jpg",
        ],
        "relationship_visual_context": [
            "original_media/images/0009_518358127_10239403542332691_492654574162600506_n.jpg",
            "original_media/images/0012_518324759_10239403542972707_7833994978016498404_n.jpg",
        ],
        "reject_images_no_person_or_low_info": [
            "original_media/images/0002_470204217_10170467431985235_4457531968548814483_n.jpg",
            "original_media/images/0010_518345840_10239403542612698_8595195393629582576_n.jpg",
            "original_media/images/0011_518331995_10239403542772702_4076019316257215825_n.jpg",
            "original_media/images/image_27bef3f70053c95f.jpg",
            "original_media/images/image_4a1adfac9355d673.jpg",
            "original_media/images/image_e30ebc4a6a82f52a.jpg",
        ],
    },
    "02_belibisamantha": {
        "person_visual_candidates": [
            "original_media/images/image_15892dec3150a2fa.jpg",
            "original_media/images/image_5c986fa64b5a88fa.jpg",
            "original_media/images/image_61889ecf929f75ba.jpg",
            "original_media/images/image_7b5e3dfdb642f6ae.jpg",
            "original_media/images/image_b4582ffeb2daad46.jpg",
            "original_media/images/image_fabdfb312e3111e6.jpg",
        ],
        "relationship_visual_context": [
            "original_media/images/image_33270b9c4814703b.jpg",
            "original_media/images/image_470f4f91ef0ccc9c.jpg",
            "original_media/images/image_71e234c9f475f8ae.jpg",
        ],
        "content_visual_context": [
            "original_media/images/image_6e399f3769f535f9.jpg",
            "original_media/images/image_c02ad1cfd9d6934e.jpg",
        ],
        "reject_images_no_person_or_low_info": [
            "original_media/images/image_0b98ac9a58a4ed49.jpg",
            "original_media/images/image_a1dabc4657a6fab9.jpg",
            "original_media/images/image_e21fb1dc155dc7fd.jpg",
        ],
    },
    "03_profile_61590550622121": {
        "person_visual_candidates": [
            "original_media/images/image_09d84242af5f18c8.jpg",
            "original_media/images/image_1099ae30135011e3.jpg",
            "original_media/images/image_136819edb0a7f15e.jpg",
            "original_media/images/image_21368dd84773bcf2.jpg",
            "original_media/images/image_33107f52c35fa924.jpg",
            "original_media/images/image_43e87d37c597f075.jpg",
            "original_media/images/image_4b0343579d7d5d3c.jpg",
            "original_media/images/image_5616baf03bc66b74.jpg",
            "original_media/images/image_5ad535893093ad00.jpg",
            "original_media/images/image_74a5de354d6e2d70.jpg",
            "original_media/images/image_9ae541726f3473cc.jpg",
            "original_media/images/image_a57fb0eb2a53c072.jpg",
            "original_media/images/image_b80e548b0e1e02bc.jpg",
            "original_media/images/image_daa994299e61cfe4.jpg",
            "original_media/images/image_e05307837de7273a.jpg",
        ],
        "relationship_visual_context": [
            "original_media/images/image_1f7fa89094009acd.jpg",
            "original_media/images/image_36435b8d2083b7b5.jpg",
            "original_media/images/image_42967ae73a0798e8.jpg",
            "original_media/images/image_4dc31c37e9bf4a27.jpg",
            "original_media/images/image_66ea713555eb5fc0.jpg",
            "original_media/images/image_8fa0fa6bbd88dbf1.jpg",
        ],
        "content_visual_context": [
            "original_media/images/image_568f676e344c44b5.jpg",
        ],
        "reject_images_no_person_or_low_info": [],
    },
    "04_lisa_panetta_official": {
        "person_visual_candidates": [
            "original_media/images/image_33bea8813a1c97c1.jpg",
            "original_media/images/image_42f18c2638ac4725.jpg",
            "original_media/images/image_49184d0ef28cd609.jpg",
            "original_media/images/image_56c498f27bc46a48.jpg",
            "original_media/images/image_653010960991978e.jpg",
            "original_media/images/image_7016218a80c719da.jpg",
            "original_media/images/image_82c3f3a55f0fff93.jpg",
            "original_media/images/image_a0ab815a51d8f41c.jpg",
            "original_media/images/image_b79e14aa06925fa2.jpg",
            "original_media/images/image_b8c0ddbda218dcbe.jpg",
            "original_media/images/image_c4c427cfd963e2f4.jpg",
            "original_media/images/image_d2d1dccd2edf1700.jpg",
            "original_media/images/image_d740b2e9e62cd2ca.jpg",
            "original_media/images/image_ee2af0bfc32a2c71.jpg",
        ],
        "relationship_visual_context": [
            "original_media/images/image_7d2cfea26c7b724a.jpg",
        ],
        "reject_images_no_person_or_low_info": [
            "original_media/images/image_37fc64a8fd625bae.jpg",
        ],
    },
}


VIDEO_DECISIONS = {
    "01_ray_hunt": {
        "scene_videos_not_face_or_voice_candidates": [
            "original_media/videos/facebook_video_549588384092707.mp4",
            "original_media/videos/facebook_video_661768406191264.mp4",
        ],
        "voice_rejected_audio_tracks": [
            "original_media/tracks/audio/549588384092707_8d565217e1d92b44.m4a",
            "original_media/tracks/audio/661768406191264_564609681d923ce6.m4a",
        ],
    },
    "02_belibisamantha": {
        "person_video_candidates": [
            "original_media/videos/facebook_video_1590277299385438.mp4",
        ],
        "voice_candidate_tracks_needs_asr": [
            "original_media/tracks/audio/1590277299385438_d1a9132d7a29853c.m4a",
        ],
        "reject_unmatched_audio_tracks": [
            "original_media/tracks/audio/2587058061759524_bc717e2b883d7c76.m4a",
        ],
    },
    "03_profile_61590550622121": {
        "person_video_candidates": [
            "original_media/videos/facebook_video_2052229975380597.mp4",
        ],
        "voice_candidate_tracks_needs_asr": [
            "original_media/tracks/audio/2052229975380597_08942a7b8e745249.m4a",
        ],
        "reject_unmatched_audio_tracks": [
            "original_media/tracks/audio/1603389238034264_b356cf9f263b1527.m4a",
        ],
    },
    "04_lisa_panetta_official": {
        "reject_unmatched_audio_tracks": [
            "original_media/tracks/audio/1542289293732271_9b1d60bf84eb1a33.m4a",
            "original_media/tracks/audio/unknown_32f7b20014d23406.m4a",
        ],
    },
}


def rel(path: Path, base: Path) -> str:
    return str(path.relative_to(base)).replace("\\", "/")


def ensure_inside(path: Path, base: Path) -> None:
    resolved = path.resolve()
    base_resolved = base.resolve()
    if base_resolved not in (resolved, *resolved.parents):
        raise ValueError(f"path escapes data root: {path}")


def media_info(path: Path) -> dict:
    info = {"exists": path.exists()}
    if not path.exists():
        return info
    info["bytes"] = path.stat().st_size
    if FFPROBE.exists() and path.suffix.lower() in {".mp4", ".m4a", ".wav", ".mp3"}:
        cmd = [
            str(FFPROBE),
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height",
            "-of",
            "json",
            str(path),
        ]
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=False)
            if result.stdout.strip():
                info["ffprobe"] = json.loads(result.stdout)
        except Exception as exc:
            info["ffprobe_error"] = str(exc)
    return info


def move_to_rejected(account_dir: Path, source_rel: str, category: str, reason: str) -> dict:
    src = account_dir / source_rel
    ensure_inside(src, ROOT)
    record = {
        "source": source_rel,
        "category": category,
        "reason": reason,
        "source_exists": src.exists(),
    }
    if not src.exists():
        return record
    dst = account_dir / "rejected_media" / category / src.name
    ensure_inside(dst, ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst = dst.with_name(f"{dst.stem}_duplicate{dst.suffix}")
    shutil.move(str(src), str(dst))
    record["moved_to"] = rel(dst, account_dir)
    return record


def collect_existing(account_dir: Path, items: list[str]) -> list[dict]:
    rows = []
    for item in items:
        path = account_dir / item
        rows.append({"path": item, "info": media_info(path)})
    return rows


def legacy_recordings(account_dir: Path) -> list[str]:
    audio_dir = account_dir / "videos" / "audio"
    if not audio_dir.exists():
        return []
    return [rel(path, account_dir) for path in sorted(audio_dir.glob("*")) if path.is_file()]


def curate_account(account_dir: Path) -> dict:
    slug = account_dir.name
    images = IMAGE_DECISIONS.get(slug, {})
    videos = VIDEO_DECISIONS.get(slug, {})
    rejected = []
    for source_rel in images.get("reject_images_no_person_or_low_info", []):
        rejected.append(
            move_to_rejected(
                account_dir,
                source_rel,
                "images_no_person_or_low_info",
                "No usable human face/person feature visible, or only low-information scenery/object media.",
            )
        )
    for source_rel in videos.get("reject_unmatched_audio_tracks", []):
        rejected.append(
            move_to_rejected(
                account_dir,
                source_rel,
                "audio_unmatched_or_no_visible_speaker",
                "Audio track has no matching downloaded video/visible speaker, so it is not usable as a voice candidate.",
            )
        )
    for source_rel in legacy_recordings(account_dir):
        rejected.append(
            move_to_rejected(
                account_dir,
                source_rel,
                "legacy_screen_recordings",
                "Old screen/system recording is mixed and not the clean original Facebook media file.",
            )
        )

    report = {
        "account_slug": slug,
        "account_dir": str(account_dir),
        "curated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "identity_boundary": "No face recognition or voiceprint identity verification is performed.",
            "visual_rule": "Keep clear foreground people as feature candidates; keep multi-person images as relationship context; reject no-person/low-information media.",
            "audio_rule": "Keep only audio aligned with a visible person video as a voice candidate needing ASR/manual review; reject unmatched tracks and legacy mixed recordings.",
        },
        "kept": {
            "person_visual_candidates": collect_existing(account_dir, images.get("person_visual_candidates", [])),
            "relationship_visual_context": collect_existing(account_dir, images.get("relationship_visual_context", [])),
            "content_visual_context": collect_existing(account_dir, images.get("content_visual_context", [])),
            "person_video_candidates": collect_existing(account_dir, videos.get("person_video_candidates", [])),
            "scene_videos_not_face_or_voice_candidates": collect_existing(
                account_dir, videos.get("scene_videos_not_face_or_voice_candidates", [])
            ),
            "voice_candidate_tracks_needs_asr": collect_existing(
                account_dir, videos.get("voice_candidate_tracks_needs_asr", [])
            ),
            "voice_rejected_but_kept_as_scene_audio": collect_existing(
                account_dir, videos.get("voice_rejected_audio_tracks", [])
            ),
        },
        "rejected_media_moved": rejected,
    }
    (account_dir / "media_curation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    accounts = [path for path in sorted(ROOT.iterdir()) if path.is_dir() and path.name.startswith(("01_", "02_", "03_", "04_"))]
    reports = [curate_account(account) for account in accounts]
    summary = {
        "curated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "accounts": reports,
        "review_contact_sheets": str(ROOT / "_curation_review"),
    }
    (ROOT / "curation_report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(ROOT / "curation_report.json")


if __name__ == "__main__":
    main()
