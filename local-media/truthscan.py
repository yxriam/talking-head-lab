"""Optional TruthScan video cross-check. The API key is read from the service environment."""

import os
import time
from pathlib import Path

import httpx

BASE = "https://detect-video.truthscan.com"
SUPPORTED = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def ready():
    configured = bool(os.environ.get("TRUTHSCAN_API_KEY", "").strip())
    return configured, "" if configured else "尚未配置 TruthScan API 密钥"


def detect(path, progress=None):
    path = Path(path)
    key = os.environ.get("TRUTHSCAN_API_KEY", "").strip()
    if not key:
        raise ValueError("TruthScan API 密钥未配置")
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError("TruthScan 仅支持 MP4、MOV、AVI、MKV 和 WebM 视频")
    if path.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("TruthScan 云端复核要求视频小于 100 MB")

    progress = progress or (lambda *_: None)
    progress(80, "正在提交 TruthScan 免费云端复核")
    with httpx.Client(timeout=httpx.Timeout(120, connect=20)) as client:
        with path.open("rb") as stream:
            response = client.post(
                f"{BASE}/detect-file",
                headers={"key": key, "accept": "application/json"},
                files={"file": (path.name, stream, "video/mp4")},
                data={"model": "generic"},
            )
        response.raise_for_status()
        job = response.json()
        job_id = job.get("id")
        if not job_id:
            raise RuntimeError("TruthScan 未返回任务编号")

        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            progress(87, "TruthScan 正在分析视频")
            status_response = client.post(
                f"{BASE}/query",
                headers={"accept": "application/json", "Content-Type": "application/json"},
                json={"id": job_id},
            )
            status_response.raise_for_status()
            result = status_response.json()
            if result.get("status") == "done":
                aggregate = result.get("result_details", {}).get("ml", {}).get("aggregate", {})
                probability = aggregate.get("prob_fake", result.get("result"))
                if probability is None:
                    raise RuntimeError("TruthScan 未返回机器学习概率")
                probability = min(1.0, max(0.0, float(probability)))
                failed = probability >= 0.5
                return {
                    "id": "truthscan", "name": "TruthScan Generic", "status": "done",
                    "verdict": "未通过：AI 倾向" if failed else "通过：真实倾向",
                    "decision": "fail" if failed else "pass", "passed": not failed,
                    "score": probability, "ai_probability": probability,
                    "real_probability": 1.0 - probability,
                    "confidence": max(probability, 1.0 - probability), "primary": False,
                    "principle": "使用 TruthScan 的通用视频机器学习模型进行独立云端复核。",
                    "paper": "https://truthscan.com/truthscan-ai-video-detection-api-documentation",
                    "threshold_text": "机器学习伪造概率 ≥ 50% 时记为 AI 倾向",
                    "evidence": {
                        "area": "整段视频",
                        "explanation": "接口只返回整段视频的机器学习聚合概率，没有提供可核验的逐帧时间定位。",
                        "high": [], "low": [],
                    },
                    "metrics": {"云端采样帧数": aggregate.get("n_frames", 0)},
                }
            if result.get("status") == "failed":
                raise RuntimeError("TruthScan 云端分析失败")
            time.sleep(2)
    raise TimeoutError("TruthScan 云端复核等待超过 10 分钟")

