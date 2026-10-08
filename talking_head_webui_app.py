import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import cv2
import gradio as gr
import numpy as np
from PIL import Image, ImageOps


APP_ROOT = Path("/root/talking_head_webui")
WORK_ROOT = Path("/root/chatterbox_outputs/webui_jobs")
SADTALKER_ROOT = Path("/root/autodl-tmp/SadTalker")
SADTALKER_PY = Path("/root/autodl-tmp/conda_envs/sadtalker/bin/python")
CHATTERBOX_PY = Path("/root/miniconda3/envs/Chatterbox/bin/python")
CHATTERBOX_SCRIPT = APP_ROOT / "chatterbox_generate.py"
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"

DEFAULT_VISUAL_NOTICE = "AI"


def run_cmd(cmd, cwd=None, env=None, timeout=None):
    started = time.time()
    proc = subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    elapsed = time.time() - started
    output = proc.stdout.strip()
    if proc.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(str(x) for x in cmd)
            + f"\nElapsed: {elapsed:.1f}s\n"
            + output[-5000:]
        )
    return output


def make_job_dir():
    job_id = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    job_dir = WORK_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    return job_id, job_dir


def normalize_text(text):
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        raise ValueError("Please enter the words to speak.")
    if len(text) > 900:
        raise ValueError("Text is too long. Keep it under about 900 characters.")
    return text


def copy_upload(src, dst):
    src = Path(src)
    if not src.exists():
        raise ValueError(f"Missing upload: {src}")
    shutil.copy2(src, dst)
    return dst


def largest_face_box(image_rgb):
    gray = cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(40, 40))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    return int(x), int(y), int(w), int(h)


def crop_with_margin(image, box, margin):
    x, y, w, h = box
    cx = x + w / 2
    cy = y + h / 2
    side = max(w, h) * (1 + margin)
    left = max(0, int(cx - side / 2))
    top = max(0, int(cy - side / 2))
    right = min(image.width, int(cx + side / 2))
    bottom = min(image.height, int(cy + side / 2))
    return image.crop((left, top, right, bottom))


def center_square(image):
    side = min(image.width, image.height)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    return image.crop((left, top, left + side, top + side))


def resize_reasonably(image, max_side):
    max_dim = max(image.width, image.height)
    if max_dim == 0:
        raise ValueError("Invalid image.")
    target = int(max_side)
    if max_dim == target:
        return image
    scale = target / max_dim
    new_size = (max(2, int(image.width * scale)), max(2, int(image.height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def prepare_image(image_path, crop_mode, max_side, job_dir):
    original = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
    crop_note = "kept full image"

    if crop_mode == "Auto face crop":
        box = largest_face_box(original)
        if box:
            original = crop_with_margin(original, box, margin=1.35)
            crop_note = "auto face crop"
        else:
            original = center_square(original)
            crop_note = "face not detected; used center square"
    elif crop_mode == "Center square":
        original = center_square(original)
        crop_note = "center square crop"

    prepared = resize_reasonably(original, max_side=max_side)
    out_path = job_dir / "source_prepared.jpg"
    prepared.save(out_path, quality=94, subsampling=0)
    return out_path, crop_note


def extract_reference_audio(media_path, start_seconds, prompt_seconds, job_dir):
    out_path = job_dir / "reference_voice_24k.wav"
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
    if start_seconds and start_seconds > 0:
        cmd += ["-ss", f"{float(start_seconds):.2f}"]
    cmd += ["-i", media_path]
    if prompt_seconds and prompt_seconds > 0:
        cmd += ["-t", f"{float(prompt_seconds):.2f}"]
    cmd += [
        "-vn",
        "-ac",
        "1",
        "-ar",
        "24000",
        "-af",
        "highpass=f=80,lowpass=f=7600,loudnorm=I=-18:TP=-2:LRA=11",
        out_path,
    ]
    run_cmd(cmd, timeout=180)
    return out_path


def generate_voice(text, prompt_wav, temperature, exaggeration, cfg_weight, job_dir):
    out_path = job_dir / "generated_voice_pcm16.wav"
    env = os.environ.copy()
    env["HF_ENDPOINT"] = "https://hf-mirror.com"
    env["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    cmd = [
        CHATTERBOX_PY,
        CHATTERBOX_SCRIPT,
        "--text",
        text,
        "--prompt",
        prompt_wav,
        "--out",
        out_path,
        "--temperature",
        f"{float(temperature):.3f}",
        "--exaggeration",
        f"{float(exaggeration):.3f}",
        "--cfg-weight",
        f"{float(cfg_weight):.3f}",
    ]
    log = run_cmd(cmd, env=env, timeout=900)
    return out_path, log


def run_sadtalker(audio_path, image_path, preprocess, pose_style, expression_scale, job_dir):
    out_base = job_dir / "sadtalker"
    out_base.mkdir(parents=True, exist_ok=True)
    cmd = [
        SADTALKER_PY,
        "inference.py",
        "--driven_audio",
        audio_path,
        "--source_image",
        image_path,
        "--checkpoint_dir",
        SADTALKER_ROOT / "checkpoints",
        "--result_dir",
        out_base,
        "--size",
        "512",
        "--preprocess",
        preprocess,
        "--pose_style",
        str(int(pose_style)),
        "--expression_scale",
        f"{float(expression_scale):.3f}",
        "--batch_size",
        "2",
    ]
    log = run_cmd(cmd, cwd=SADTALKER_ROOT, timeout=2400)
    candidates = sorted(out_base.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError("SadTalker finished but no mp4 was found.")
    return candidates[0], log


def add_visual_notice(raw_video, job_dir, visual_notice_text):
    final_video = job_dir / "talking_head_output.mp4"
    preview = job_dir / "preview.jpg"
    visual_notice_text = re.sub(r"[^A-Za-z0-9 _.-]", "", (visual_notice_text or "").strip())
    if not visual_notice_text:
        visual_notice_text = DEFAULT_VISUAL_NOTICE
    vf = (
        f"drawtext=text={visual_notice_text}:x=18:y=18:fontsize=30:"
        "fontcolor=white:box=1:boxcolor=black@0.45"
    )
    run_cmd(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            raw_video,
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            final_video,
        ],
        timeout=300,
    )
    run_cmd(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "00:00:04",
            "-i",
            final_video,
            "-frames:v",
            "1",
            preview,
        ],
        timeout=60,
    )
    return final_video, preview


def generate(
    image_file,
    voice_media,
    text,
    authorized,
    crop_mode,
    preprocess,
    visual_notice_text,
    prompt_start,
    prompt_duration,
    pose_style,
    expression_scale,
    image_max_side,
    temperature,
    exaggeration,
    cfg_weight,
):
    if not authorized:
        raise gr.Error("You must confirm that you have consent to use this person's image and voice.")
    if not image_file:
        raise gr.Error("Please upload a face image.")
    if not voice_media:
        raise gr.Error("Please upload an audio or video file for the voice reference.")

    job_id, job_dir = make_job_dir()
    status = [f"Job `{job_id}` started."]
    try:
        yield "\n\n".join(status), None, None, None

        text = normalize_text(text)
        status.append("Text normalized.")
        yield "\n\n".join(status), None, None, None

        uploaded_image = copy_upload(image_file, job_dir / "input_image")
        uploaded_voice = copy_upload(voice_media, job_dir / ("input_voice" + Path(voice_media).suffix))
        prepared_image, crop_note = prepare_image(uploaded_image, crop_mode, int(image_max_side), job_dir)
        status.append(f"Image prepared: {crop_note}.")
        yield "\n\n".join(status), None, None, str(prepared_image)

        prompt_wav = extract_reference_audio(uploaded_voice, prompt_start, prompt_duration, job_dir)
        status.append(f"Voice reference extracted: `{prompt_wav.name}`.")
        yield "\n\n".join(status), None, None, str(prepared_image)

        generated_wav, cb_log = generate_voice(text, prompt_wav, temperature, exaggeration, cfg_weight, job_dir)
        status.append("Chatterbox voice generated.")
        yield "\n\n".join(status), None, str(generated_wav), str(prepared_image)

        raw_video, st_log = run_sadtalker(
            generated_wav,
            prepared_image,
            preprocess,
            int(pose_style),
            float(expression_scale),
            job_dir,
        )
        status.append("SadTalker video rendered.")
        yield "\n\n".join(status), None, str(generated_wav), str(prepared_image)

        final_video, preview = add_visual_notice(raw_video, job_dir, visual_notice_text)
        status.append(f"Done. Output: `{final_video}`")
        yield "\n\n".join(status), str(final_video), str(generated_wav), str(preview)
        return
    except Exception as exc:
        status.append(f"ERROR: {exc}")
        raise gr.Error("\n\n".join(status))


CSS = """
.compact-note { font-size: 0.92rem; color: #4b5563; }
"""


with gr.Blocks(title="Talking Head Demo Builder", css=CSS) as demo:
    gr.Markdown("## Talking Head Demo Builder")
    gr.Markdown(
        "Upload a face image, a voice reference audio/video, and text. "
        "A configurable visual notice is rendered on the video output."
    )

    with gr.Row():
        with gr.Column(scale=1):
            image_file = gr.Image(
                label="Face image",
                type="filepath",
                sources=["upload", "clipboard"],
            )
            voice_media = gr.File(
                label="Voice reference audio or video",
                file_types=[".wav", ".mp3", ".m4a", ".aac", ".flac", ".mp4", ".mov", ".webm", ".mkv"],
                type="filepath",
            )
            text = gr.Textbox(
                label="Text to speak",
                lines=5,
                placeholder="Type the message to synthesize.",
            )
            authorized = gr.Checkbox(
                label="I have consent to use this person's image and voice.",
                value=False,
            )
            run_button = gr.Button("Generate Video", variant="primary")

        with gr.Column(scale=1):
            output_video = gr.Video(label="Generated video", format="mp4", autoplay=False)
            output_audio = gr.Audio(label="Generated speech", type="filepath")
            output_preview = gr.Image(label="Prepared/preview image", type="filepath")
            status = gr.Markdown(label="Status")

    with gr.Accordion("Advanced controls", open=False):
        with gr.Row():
            crop_mode = gr.Dropdown(
                ["Keep full image", "Auto face crop", "Center square"],
                value="Keep full image",
                label="Image crop mode",
            )
            preprocess = gr.Dropdown(
                ["extfull", "extcrop", "crop", "resize", "full"],
                value="extfull",
                label="SadTalker preprocess",
            )
            visual_notice_text = gr.Textbox(
                value=DEFAULT_VISUAL_NOTICE,
                label="Visual notice text",
                info="Temporary placeholder for the future icon/warning layer.",
            )
            image_max_side = gr.Slider(512, 1600, value=1024, step=64, label="Prepared image max side")
        with gr.Row():
            prompt_start = gr.Number(value=0, precision=1, label="Voice prompt start seconds")
            prompt_duration = gr.Number(value=24, precision=1, label="Voice prompt duration seconds")
        with gr.Row():
            pose_style = gr.Slider(0, 45, value=12, step=1, label="Pose style")
            expression_scale = gr.Slider(0.8, 1.4, value=1.05, step=0.05, label="Expression scale")
        with gr.Row():
            temperature = gr.Slider(0.35, 0.95, value=0.55, step=0.05, label="TTS temperature")
            exaggeration = gr.Slider(0.1, 0.8, value=0.25, step=0.05, label="TTS exaggeration")
            cfg_weight = gr.Slider(0.2, 0.8, value=0.45, step=0.05, label="TTS CFG weight")

    run_button.click(
        generate,
        inputs=[
            image_file,
            voice_media,
            text,
            authorized,
            crop_mode,
            preprocess,
            visual_notice_text,
            prompt_start,
            prompt_duration,
            pose_style,
            expression_scale,
            image_max_side,
            temperature,
            exaggeration,
            cfg_weight,
        ],
        outputs=[status, output_video, output_audio, output_preview],
        concurrency_limit=1,
    )


if __name__ == "__main__":
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    demo.queue(max_size=4, default_concurrency_limit=1)
    demo.launch(
        server_name=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.environ.get("GRADIO_SERVER_PORT", "7860")),
        share=False,
    )
