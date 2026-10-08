from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import subprocess

ROOT = Path(r"D:\desktop\exam\cv\facebook-scam\data\accounts")
REVIEW = ROOT / "_curation_review"
FFMPEG = Path(r"D:\documents\UC\facebook\tools\ffmpeg_extract\ffmpeg-9.0-essentials_build\bin\ffmpeg.exe")


def load_font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


FONT = load_font(16)
SMALL = load_font(13)


def make_sheet(files, out, title, thumb=(180, 180), cols=4):
    files = list(files)
    if not files:
        return
    rows = math.ceil(len(files) / cols)
    label_h = 58
    width = cols * thumb[0]
    height = 42 + rows * (thumb[1] + label_h)
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), title, fill="black", font=FONT)
    for i, file in enumerate(files):
        x = (i % cols) * thumb[0]
        y = 42 + (i // cols) * (thumb[1] + label_h)
        try:
            with Image.open(file) as opened:
                original_size = opened.size
                image = opened.convert("RGB")
            image.thumbnail((thumb[0] - 8, thumb[1] - 8))
            bx = x + (thumb[0] - image.width) // 2
            by = y + (thumb[1] - image.height) // 2
            sheet.paste(image, (bx, by))
            draw.text((x + 4, y + thumb[1] + 3), f"{i + 1:02d} {file.name[:24]}", fill="black", font=SMALL)
            draw.text((x + 4, y + thumb[1] + 22), f"{original_size[0]}x{original_size[1]} {file.stat().st_size // 1024}KB", fill="gray", font=SMALL)
        except Exception as exc:
            draw.text((x + 4, y + 4), f"ERR {file.name}: {exc}", fill="red", font=SMALL)
    sheet.save(out, quality=92)


def extract_video_frames(account, videos):
    frame_dir = REVIEW / f"{account.name}_video_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for video in videos:
        for sec in (1, 5, 10, 20):
            out = frame_dir / f"{video.stem}_t{sec}.png"
            subprocess.run(
                [
                    str(FFMPEG),
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-ss",
                    str(sec),
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    str(out),
                ],
                check=False,
            )
            if out.exists():
                frames.append(out)
    return frames


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    for account in sorted([item for item in ROOT.iterdir() if item.is_dir() and item.name != "_curation_review"]):
        images = sorted((account / "original_media" / "images").glob("*"))
        make_sheet(images, REVIEW / f"{account.name}_images_sheet.jpg", f"{account.name} original images")
        videos = sorted((account / "original_media" / "videos").glob("facebook_video_*.mp4"))
        frames = extract_video_frames(account, videos)
        make_sheet(frames, REVIEW / f"{account.name}_videos_sheet.jpg", f"{account.name} muxed video frames", thumb=(220, 160), cols=3)
    print(REVIEW)


if __name__ == "__main__":
    main()
