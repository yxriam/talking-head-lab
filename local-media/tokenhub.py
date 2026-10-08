"""TokenHub HumanActor adapter with temporary Tencent COS storage."""

import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SUBMIT_URL = "https://tokenhub.tencentmaas.com/v1/api/video/submit"
QUERY_URL = "https://tokenhub.tencentmaas.com/v1/api/video/query"
MODEL = "yt-video-humanactor"


def configuration():
    names = (
        "TOKENHUB_API_KEY",
        "TENCENT_COS_SECRET_ID",
        "TENCENT_COS_SECRET_KEY",
        "TENCENT_COS_REGION",
        "TENCENT_COS_BUCKET",
    )
    values = {name: os.environ.get(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    return values, missing


def ready():
    _, missing = configuration()
    if missing:
        return False, "TokenHub 或 COS 尚未配置"
    try:
        import qcloud_cos  # noqa: F401
    except ImportError:
        return False, "尚未安装腾讯 COS Python SDK"
    return True, ""


def _post(url, payload, api_key, timeout=60):
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[-2000:]
        raise RuntimeError(f"TokenHub 请求失败（HTTP {error.code}）：{detail}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"无法连接 TokenHub：{error}") from error


def _cos_client(settings):
    from qcloud_cos import CosConfig, CosS3Client

    config = CosConfig(
        Region=settings["TENCENT_COS_REGION"],
        SecretId=settings["TENCENT_COS_SECRET_ID"],
        SecretKey=settings["TENCENT_COS_SECRET_KEY"],
        Scheme="https",
    )
    return CosS3Client(config)


def _download(url, destination):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise RuntimeError("TokenHub 返回了无效的视频地址")
    temporary = destination.with_suffix(".download")
    try:
        request = Request(url, headers={"User-Agent": "local-media/1.0"})
        with urlopen(request, timeout=300) as response, temporary.open("wb") as output:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 1024 * 1024 * 1024:
                    raise RuntimeError("TokenHub 返回的视频超过 1 GB")
                output.write(chunk)
        if not temporary.stat().st_size:
            raise RuntimeError("TokenHub 返回了空视频")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def generate(image_path, audio_path, output_path, on_progress=lambda value, message: None):
    """Generate one video and persist the expiring cloud result locally."""
    settings, missing = configuration()
    if missing:
        raise RuntimeError("缺少配置：" + "、".join(missing))

    image_path = Path(image_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    if image_path.stat().st_size > 10_000_000:
        raise ValueError("人像照片需小于 10 MB")
    if audio_path.stat().st_size > 10_000_000:
        raise ValueError("驱动音频需小于 10 MB")

    cos = _cos_client(settings)
    bucket = settings["TENCENT_COS_BUCKET"]
    state_path = output_path.parent / "tokenhub-job.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    job_id = state.get("id")
    audio_object_key = state.get("audio_object_key") or state.get("object_key")
    image_object_key = state.get("image_object_key")
    try:
        if not job_id:
            batch = uuid.uuid4().hex
            audio_object_key = f"media-app-input/{batch}-audio{audio_path.suffix.lower()}"
            image_object_key = f"media-app-input/{batch}-image{image_path.suffix.lower()}"
            on_progress(7, "正在临时上传人像与驱动语音")
            audio_content_type = mimetypes.guess_type(audio_path.name)[0] or "application/octet-stream"
            cos.upload_file(Bucket=bucket, LocalFilePath=str(audio_path), Key=audio_object_key,
                            ContentType=audio_content_type)
            image_content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
            cos.upload_file(Bucket=bucket, LocalFilePath=str(image_path), Key=image_object_key,
                            ContentType=image_content_type)
            audio_url = cos.get_presigned_download_url(Bucket=bucket, Key=audio_object_key, Expired=7200)
            image_url = cos.get_presigned_download_url(Bucket=bucket, Key=image_object_key, Expired=7200)
            payload = {
                "model": MODEL,
                "prompt": ("正方形头肩构图中的人物正对镜头自然讲话，保持人物身份和原始构图。仅做轻微自然的眨眼、"
                           "表情与头部动作，肩部基本静止；镜头和背景完全固定，不运镜、不缩放、不重新构图、不改变背景。"),
                # TokenHub's OpenAI-compatible endpoint requires snake_case keys.
                "audio_url": audio_url,
                "image_url": image_url,
                "resolution": "720p",
                "frame_rate": 25,
                "logo_add": 0,
            }
            on_progress(15, "正在提交 TokenHub 人像任务")
            submitted = _post(SUBMIT_URL, payload, settings["TOKENHUB_API_KEY"])
            job_id = submitted.get("id")
            if not job_id:
                error = submitted.get("error") or {}
                detail = error.get("message") or submitted.get("message") or "未返回任务编号"
                request_id = submitted.get("request_id")
                suffix = f"（请求 ID：{request_id}）" if request_id else ""
                raise RuntimeError(f"TokenHub 提交失败：{detail}{suffix}")
            state_path.write_text(
                json.dumps({"id": job_id, "audio_object_key": audio_object_key,
                            "image_object_key": image_object_key}, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            on_progress(20, "正在继续上次 TokenHub 人像任务")

        started = time.monotonic()
        while True:
            if time.monotonic() - started > 3600:
                raise TimeoutError("TokenHub 人像任务等待超过一小时")
            time.sleep(4)
            result = _post(QUERY_URL, {"model": MODEL, "id": job_id}, settings["TOKENHUB_API_KEY"])
            status = str(result.get("status", "")).lower()
            reported = result.get("progress")
            if isinstance(reported, (int, float)):
                progress = min(92, 20 + int(reported) * 72 // 100)
            else:
                progress = min(88, 20 + int(time.monotonic() - started) // 6)
            on_progress(progress, "TokenHub 正在生成自然人像视频")
            if status == "completed":
                video_url = (result.get("data") or {}).get("url")
                if not video_url:
                    raise RuntimeError(f"TokenHub 任务完成但没有视频地址：{result}")
                on_progress(94, "正在将生成视频保存到本地")
                _download(video_url, output_path)
                return
            if status in {"failed", "cancelled", "canceled"}:
                error = result.get("error") or result.get("message") or "未知错误"
                raise RuntimeError(f"TokenHub 生成人像失败：{error}")
    finally:
        for object_key in (audio_object_key, image_object_key):
            try:
                if object_key:
                    cos.delete_object(Bucket=bucket, Key=object_key)
            except Exception:
                pass
