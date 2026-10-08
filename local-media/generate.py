"""Model subprocess: keeps GPU memory isolated between voice and video jobs."""

import json
import math
import os
import subprocess
import sys
import uuid
from pathlib import Path

from video_profiles import video_profile

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HOME", "/opt/media-models/huggingface")


def run(*args, cwd=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def voice(inputs, work):
    import re
    import soundfile as sf
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    prompt = work / "reference.wav"
    run("ffmpeg", "-nostdin", "-y", "-i", inputs["audio"], "-map", "0:a:0", "-vn", "-t", "20", "-ac", "1", "-ar", "24000", prompt)
    language = "zh" if re.search(r"[\u4e00-\u9fff]", inputs["text"]) else "en"
    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
    with torch.inference_mode():
        wav = model.generate(inputs["text"], language_id=language, audio_prompt_path=str(prompt))
    sf.write(work / "output.wav", wav.squeeze(0).cpu().numpy(), model.sr, subtype="PCM_16")


def probe_duration(path):
    info = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "default=nw=1:nk=1", str(path)], text=True)
    return float(info)


def finish_video(source, output, policy):
    """Preserve native model pixels unless the renderer itself adds padding."""
    if policy == "native":
        run("ffmpeg", "-nostdin", "-y", "-i", source, "-c:v", "copy", "-c:a", "aac",
            "-movflags", "+faststart", output)
        return
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(source),
    ], text=True)
    stream = json.loads(raw)["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])
    side = min(width, height)
    left, top = (width - side) // 2, (height - side) // 2
    run("ffmpeg", "-nostdin", "-y", "-i", source,
        "-vf", f"crop={side}:{side}:{left}:{top},setsar=1",
        "-c:v", "libx264", "-crf", "18", "-c:a", "aac",
        "-movflags", "+faststart", output)


def sadtalker_video(inputs, work, models, audio):
    root = models / "SadTalker"
    assets = work / "gfpgan"
    if not assets.exists():
        assets.symlink_to(root / "gfpgan", target_is_directory=True)
    results = work / ("render-" + uuid.uuid4().hex)
    results.mkdir()
    run(sys.executable, root / "inference.py", "--source_image", inputs["image"],
        "--driven_audio", audio, "--checkpoint_dir", root / "checkpoints", "--result_dir", results,
        "--size", "512", "--preprocess", "extcrop", "--pose_style", "0",
        "--expression_scale", "1.05", "--batch_size", "1", cwd=work)
    candidates = list(results.rglob("*.mp4"))
    if len(candidates) != 1:
        raise RuntimeError("无法确定模型生成的视频")
    finish_video(candidates[0], work / "output.mp4", video_profile("sadtalker")["output_policy"])


def echomimic_video(inputs, work, models, audio, duration):
    if duration > 20:
        raise ValueError("EchoMimic V1 试验模式的驱动语音需在 20 秒以内")
    root = models / "EchoMimic"
    config = work / "echomimic.yaml"
    weights = root / "pretrained_weights"
    def q(value):
        return json.dumps(str(value), ensure_ascii=False)
    config.write_text("\n".join([
        f"pretrained_base_model_path: {q(weights / 'sd-image-variations-diffusers')}",
        f"pretrained_vae_path: {q(weights / 'sd-vae-ft-mse')}",
        f"audio_model_path: {q(weights / 'audio_processor/whisper_tiny.pt')}",
        f"denoising_unet_path: {q(weights / 'denoising_unet_acc.pth')}",
        f"reference_unet_path: {q(weights / 'reference_unet.pth')}",
        f"face_locator_path: {q(weights / 'face_locator.pth')}",
        f"motion_module_path: {q(weights / 'motion_module_acc.pth')}",
        f"inference_config: {q(root / 'configs/inference/inference_v2.yaml')}",
        "weight_dtype: fp16", "test_cases:", f"  {q(inputs['image'])}:", f"    - {q(audio)}", ""
    ]), encoding="utf-8")
    env = os.environ.copy()
    env.update({"TRANSFORMERS_OFFLINE": "1", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    length = max(12, math.ceil(duration * 24 / 12) * 12)
    subprocess.run([sys.executable, "-u", str(root / "infer_audio2vid_acc.py"), "--config", str(config),
                    "-W", "512", "-H", "512", "-L", str(length), "--steps", "12", "--fps", "24",
                    "--context_frames", "24", "--context_overlap", "8"], cwd=work, env=env, check=True)
    candidates = list((work / "output").rglob("*_withaudio.mp4"))
    if len(candidates) != 1:
        raise RuntimeError("无法确定 EchoMimic V1 生成的视频")
    finish_video(candidates[0], work / "output.mp4", video_profile("echomimic_v1")["output_policy"])


def joyvasa_video(inputs, work, models, audio):
    root = models / "JoyVASA"
    results = work / ("joyvasa-" + uuid.uuid4().hex)
    results.mkdir()
    run(sys.executable, "-u", root / "inference.py",
        "--reference", inputs["image"], "--audio", audio,
        "--animation-mode", "human", "--animation-region", "all",
        "--driving-option", "expression-friendly", "--output-dir", results,
        "--no-flag-do-crop", "--no-flag-do-rot", "--flag-use-half-precision", cwd=root)
    candidates = list(results.rglob("*.mp4"))
    if len(candidates) != 1:
        raise RuntimeError("无法确定 JoyVASA 生成的视频")
    finish_video(candidates[0], work / "output.mp4", video_profile("joyvasa")["output_policy"])


def echomimic_v3_video(inputs, work, models, audio, duration):
    if duration > 4:
        raise ValueError("EchoMimic V3 Flash 在本机内存配置下限 4 秒以内")
    root = models / "EchoMimicV3"
    results = work / ("echomimic-v3-" + uuid.uuid4().hex)
    results.mkdir()
    weights = root / "weights"
    length = max(5, min(201, int(duration * 25)))
    length = (length - 1) // 4 * 4 + 1
    env = os.environ.copy()
    env.update({"TRANSFORMERS_OFFLINE": "1", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    subprocess.run([
        sys.executable, "-u", str(root / "infer_flash.py"),
        "--image_path", inputs["image"], "--audio_path", str(audio),
        "--prompt", ("A photorealistic centered head-and-shoulders portrait speaks naturally to a locked-off camera. "
                     "Keep the 1:1 composition and background completely stationary. Use subtle blinks, small natural "
                     "head motions, restrained facial expressions, and mostly still shoulders. No camera movement, zoom, "
                     "reframing, scene change, background motion, background deformation, object motion, or lighting change."),
        "--config_path", str(root / "config/config.yaml"),
        "--model_name", str(weights / "Wan2.1-Fun-V1.1-1.3B-InP"),
        "--transformer_path", str(weights / "flash/echomimicv3-flash-pro/diffusion_pytorch_model.safetensors"),
        "--wav2vec_model_dir", str(weights / "chinese-wav2vec2-base"),
        "--save_path", str(results), "--num_inference_steps", "8",
        "--video_length", str(length), "--sample_size", "384", "384",
        # Keep the diffusion path on GPU and page the conditioning encoders on
        # demand; this fits the 12 GB GPU without recreating the WSL RAM spike.
        "--fps", "25", "--GPU_memory_mode", "hybrid",
        "--weight_dtype", "bfloat16", "--enable_teacache",
    ], cwd=root, env=env, check=True)
    candidates = list(results.glob("*_output.mp4"))
    if len(candidates) != 1:
        raise RuntimeError("无法确定 EchoMimic V3 Flash 生成的视频")
    finish_video(candidates[0], work / "output.mp4", video_profile("echomimic_v3_flash")["output_policy"])


def video(inputs, work, models):
    audio = work / "driving.wav"
    run("ffmpeg", "-nostdin", "-y", "-i", inputs["audio"], "-ac", "1", "-ar", "16000", audio)
    # Bound expensive jobs before launching the renderer.
    duration = probe_duration(audio)
    if not 0 < duration <= 60:
        raise ValueError("驱动语音需在 60 秒以内")
    model = inputs.get("model", "sadtalker")
    profile = video_profile(model)
    if duration > profile["max_seconds"]:
        raise ValueError(f"所选模型的驱动语音需在 {profile['max_seconds']} 秒以内")
    if model == "echomimic_v1":
        echomimic_video(inputs, work, models, audio, duration)
    elif model == "joyvasa":
        joyvasa_video(inputs, work, models, audio)
    elif model == "echomimic_v3_flash":
        echomimic_v3_video(inputs, work, models, audio, duration)
    else:
        sadtalker_video(inputs, work, models, audio)


if __name__ == "__main__":
    kind, directory, model_root = sys.argv[1:]
    work = Path(directory)
    inputs = json.loads((work / "request.json").read_text(encoding="utf-8"))
    if kind == "voice":
        voice(inputs, work)
    elif kind == "video":
        video(inputs, work, Path(model_root))
    else:
        raise ValueError("不支持的生成任务")
