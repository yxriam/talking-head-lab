"""Local media API. Uploaded bytes stay here; GPU jobs run one at a time."""

import json
import os
import re
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import tokenhub
import truthscan
import local_account_model
from video_profiles import VIDEO_PROFILES, video_profile

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
ORIGIN = "http://localhost:3100"
ALLOWED_ORIGINS = {ORIGIN, "http://127.0.0.1:3100"}
MAX_BYTES = 500 * 1024 * 1024
ID = re.compile(r"^[a-f0-9]{32}$")
pool = ThreadPoolExecutor(max_workers=1)
lock = Lock()
jobs = {}
account_busy = False
app = FastAPI(title="Local Media", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=list(ALLOWED_ORIGINS),
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.middleware("http")
async def local_only(request: Request, call_next):
    # CORS alone does not prevent a third-party page from submitting a form.
    from fastapi.responses import JSONResponse
    if request.url.hostname not in {"localhost", "127.0.0.1", "testserver"}:
        return JSONResponse({"detail": "只允许本地访问"}, status_code=403)
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        return JSONResponse({"detail": "不允许此网页来源"}, status_code=403)
    return await call_next(request)


def folder(identifier):
    if not ID.fullmatch(identifier):
        raise HTTPException(404, "找不到文件")
    return DATA / identifier


def media(identifier):
    path = folder(identifier)
    try:
        info = json.loads((path / "media.json").read_text(encoding="utf-8"))
        if not (path / info["filename"]).is_file():
            raise FileNotFoundError()
        return info
    except (FileNotFoundError, json.JSONDecodeError):
        raise HTTPException(404, "找不到文件")


def publish(path, kind, name=None):
    info = {"id": path.parent.name, "name": name or path.name,
            "filename": path.name, "kind": kind,
            "url": f"/media/{path.parent.name}"}
    (path.parent / "media.json").write_text(json.dumps(info), encoding="utf-8")
    return info


def runtime():
    """Use native Linux in WSL; explicit local paths avoid remote execution."""
    return Path(os.environ.get("MEDIA_MODELS", "/opt/media-models"))


def capabilities():
    root = runtime()
    linux = sys.platform == "linux"
    voice = linux and (root / "chatterbox/.venv/bin/python").is_file() and (root / "chatterbox/READY").is_file()
    video = linux and (root / "SadTalker/.venv/bin/python").is_file() and (root / "SadTalker/READY").is_file()
    echo = linux and (root / "EchoMimic/.venv/bin/python").is_file() and (root / "EchoMimic/READY").is_file()
    joyvasa = linux and (root / "JoyVASA/.venv/bin/python").is_file() and (root / "JoyVASA/READY").is_file()
    echo_v3 = (linux and (root / "EchoMimicV3/.venv/bin/python").is_file()
               and (root / "EchoMimicV3/INFERENCE_VERIFIED").is_file())
    detect = (linux and (root / "DeepfakeBench/.venv/bin/python").is_file()
              and (root / "DeepfakeBench/READY").is_file()
              and (root / "NPR/READY").is_file()
              and (root / "GenD/READY").is_file())
    reason = "需先完成 WSL2 与模型安装及推理验证" if not linux else "模型尚未安装或未通过推理验证"
    cloud, cloud_reason = tokenhub.ready()
    cloud = linux and cloud
    def video_state(backend_ready, name, backend_reason=reason):
        return {"ready": bool(backend_ready), "name": name,
                "reason": "" if backend_ready else backend_reason}
    return {"voice": {"ready": bool(voice), "name": "Chatterbox", "reason": "" if voice else reason},
            "video": {"ready": bool(video or echo or joyvasa or echo_v3 or cloud), "name": "Local audio-to-head / TokenHub",
                      "reason": "" if video or echo or joyvasa or echo_v3 or cloud else reason,
                      "models": {"sadtalker": video_state(video, "SadTalker"),
                                 "echomimic_v1": video_state(echo, "EchoMimic V1"),
                                 "joyvasa": video_state(joyvasa, "JoyVASA"),
                                 "echomimic_v3_flash": video_state(echo_v3, "EchoMimic V3 Flash", "模型已下载，仍需通过本机稳定性验证"),
                                 "tokenhub_humanactor": video_state(cloud, "YT HumanActor", cloud_reason or reason)},},
            "detect": {"ready": bool(detect), "reason": "" if detect else "本地检测模型尚未全部部署，不能进行真伪判定",
                       "cloud": {"truthscan": {"ready": truthscan.ready()[0], "reason": truthscan.ready()[1]}}}}


@app.get("/health")
def health():
    with lock:
        busy=account_busy or any(job['status'] in {'queued','running'} for job in jobs.values())
    return {"status": "ok", "platform": sys.platform, "capabilities": capabilities(),
            "busy": busy,
            "account_analysis": {"ready": sys.platform=='linux' and local_account_model.ready(runtime()),
                                 "model": local_account_model.MODEL, "kind": "llm"}}


class AccountAnalysisInput(BaseModel):
    draft: list[str] = Field(min_length=1,max_length=12)
    draft_en: list[str] = Field(default_factory=list,max_length=12)
    evidence_ids: list[str] = Field(min_length=1,max_length=100)
    facts: list[dict[str,str]] = Field(default_factory=list,max_length=100)


@app.post('/account-analysis')
def account_analysis(item: AccountAnalysisInput):
    global account_busy
    if sum(map(len,item.draft))+sum(map(len,item.draft_en))/3>3600 or any(not re.fullmatch(r'E[1-9]\d*',value) for value in item.evidence_ids):
        raise HTTPException(422,'账号证据草稿过长或来源编号无效')
    if any(set(fact)!={'id','text'} or fact['id'] not in item.evidence_ids or not fact['text'] or len(fact['text'])>1500 for fact in item.facts) or sum(len(fact['text']) for fact in item.facts)>4000:
        raise HTTPException(422,'原始事实过长或来源编号无效')
    if sys.platform!='linux' or not local_account_model.ready(runtime()):
        raise HTTPException(503,'本地账号 LLM 尚未就绪')
    with lock:
        if account_busy or any(job['status'] in {'queued','running'} for job in jobs.values()):
            raise HTTPException(409,'本地 GPU 正在处理其他任务，请完成后再更新账号分析')
        account_busy=True
    try:
        return local_account_model.generate(item.draft,item.evidence_ids,runtime(),draft_en=item.draft_en,facts=item.facts)
    except (subprocess.SubprocessError,RuntimeError,ValueError) as error:
        raise HTTPException(502,'本地账号 LLM 推理失败；未用模板冒充模型结果') from error
    finally:
        with lock:
            account_busy=False


@app.post("/media")
async def upload(file: UploadFile):
    content_type = file.content_type or ""
    suffix = Path(file.filename or "").suffix.lower()
    allowed = {"image": {".jpg", ".jpeg", ".png", ".webp"},
               "audio": {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".aac"},
               "video": {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"}}
    declared = content_type.split("/")[0]
    candidates = [kind for kind, suffixes in allowed.items() if suffix in suffixes]
    kind = declared if declared in allowed and suffix in allowed[declared] else candidates[0] if declared in {"", "application"} and len(candidates) == 1 else ""
    if not kind:
        raise HTTPException(415, "不支持此文件格式")
    directory = DATA / uuid.uuid4().hex
    directory.mkdir()
    path = directory / ("input" + suffix)
    size = 0
    try:
        with path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(413, "文件需小于 500 MB")
                output.write(chunk)
        if not size:
            raise HTTPException(400, "文件为空")
        return publish(path, kind, Path(file.filename).name)
    except Exception:
        path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    finally:
        await file.close()


@app.get("/media/{identifier}")
def download(identifier: str):
    info = media(identifier)
    return FileResponse(folder(identifier) / info["filename"], filename=info["name"],
                        content_disposition_type="inline")


class JobInput(BaseModel):
    kind: str
    audio_id: str | None = None
    image_id: str | None = None
    video_id: str | None = None
    media_id: str | None = None
    text: str = Field(default="", max_length=500)
    model: str | None = None
    use_truthscan: bool = False


def require_media(identifier, kind):
    if not identifier:
        raise HTTPException(400, "缺少素材")
    info = media(identifier)
    if info["kind"] != kind:
        raise HTTPException(400, "素材类型不匹配")
    return str(folder(identifier) / info["filename"])


@app.post("/jobs")
def submit(item: JobInput):
    if item.kind not in {"voice", "video", "detect"}:
        raise HTTPException(400, "不支持此任务")
    inputs = {}
    if item.kind == "detect":
        identifier = item.media_id or item.video_id
        if not identifier:
            raise HTTPException(400, "缺少需要检测的图片或视频")
        info = media(identifier)
        if info["kind"] not in {"image", "video"}:
            raise HTTPException(400, "检测仅支持图片或视频")
        inputs["media"] = str(folder(identifier) / info["filename"])
        inputs["media_kind"] = info["kind"]
        inputs["use_truthscan"] = bool(item.use_truthscan)
    else:
        if item.kind == "voice":
            if not item.audio_id:
                raise HTTPException(400, "缺少音色克隆素材")
            info = media(item.audio_id)
            if info["kind"] not in {"audio", "video"}:
                raise HTTPException(400, "音色克隆仅支持音频或含音轨的视频")
            inputs["audio"] = str(folder(item.audio_id) / info["filename"])
            inputs["reference_kind"] = info["kind"]
            if not item.text.strip():
                raise HTTPException(400, "请输入需要说出的文字")
            inputs["text"] = item.text.strip()
        else:
            inputs["audio"] = require_media(item.audio_id, "audio")
            inputs["image"] = require_media(item.image_id, "image")
            inputs["model"] = item.model or "sadtalker"
            if inputs["model"] not in VIDEO_PROFILES:
                raise HTTPException(400, "不支持此人像视频模型")
    state = capabilities()[item.kind]
    if item.kind == "video":
        state = state.get("models", {}).get(inputs["model"], {"ready": False, "reason": "模型状态不可用"})
    if not state["ready"]:
        raise HTTPException(503, state["reason"])
    with lock:
        if account_busy or any(job["status"] in {"queued", "running"} for job in jobs.values()):
            raise HTTPException(409, "已有任务正在处理，请完成后再提交")
        identifier = uuid.uuid4().hex
        directory = DATA / identifier
        directory.mkdir()
        jobs[identifier] = {"id": identifier, "kind": item.kind, "status": "queued", "message": "等待处理", "progress": 0,
                            "model": inputs.get("model", {"voice": "chatterbox", "detect": "GenD ensemble"}.get(item.kind))}
    (directory / "request.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    pool.submit(run_job, identifier, item.kind)
    return jobs[identifier].copy()


def run_job(identifier, kind):
    directory = folder(identifier)
    inputs = json.loads((directory / "request.json").read_text(encoding="utf-8"))
    video_model = inputs.get("model", "sadtalker")
    model = {"voice":"chatterbox", "video": video_profile(video_model)["runtime"],
             "detect":"DeepfakeBench"}[kind]
    python = runtime() / model / ".venv/bin/python" if video_model != "tokenhub_humanactor" else None
    with lock:
        jobs[identifier].update(status="running", progress=3, message={"voice":"正在准备语音模型", "video":"正在分析人像与语音", "detect":"正在抽取人脸帧"}[kind])
    try:
        if kind == "video" and video_model == "tokenhub_humanactor":
            started = time.monotonic()
            normalized_audio = directory / "tokenhub-driving.wav"
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", inputs["audio"], "-ac", "1", "-ar", "16000",
                            str(normalized_audio)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            duration = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                      "-of", "default=nw=1:nk=1", str(normalized_audio)], text=True))
            if not 2 <= duration <= 60:
                raise ValueError("TokenHub 驱动语音需为 2 到 60 秒")

            def cloud_progress(progress, message):
                with lock:
                    jobs[identifier].update(progress=min(95, 3 + progress * 92 // 100), message=message)

            tokenhub.generate(inputs["image"], normalized_audio, directory / "output.mp4", cloud_progress)
        elif kind == "detect":
            command = [str(python), str(ROOT / "detect.py"), inputs["media"], str(runtime() / model), str(directory / "report.json")]
        else:
            command = [str(python), str(ROOT / "generate.py"), kind, str(directory), str(runtime())]
        if not (kind == "video" and video_model == "tokenhub_humanactor"):
            log_path = directory / "run.log"
            reported_progress = 3
            with log_path.open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                started = time.monotonic()
                while process.poll() is None:
                    if time.monotonic() - started > 3600:
                        process.kill()
                        raise TimeoutError("任务运行超过一小时")
                    time.sleep(0.5)
                    output = log_path.read_text(encoding="utf-8", errors="ignore")[-16000:]
                    progress = max(reported_progress, progress_from_log(kind, output, video_model))
                    reported_progress = progress
                    with lock:
                        jobs[identifier].update(progress=progress, message=progress_message(kind, progress, video_model))
                if process.returncode:
                    # Input checks in the worker raise ValueError; show that reason, not the command line.
                    log.flush()
                    reasons = re.findall(r"^ValueError: (.+)$", log_path.read_text(encoding="utf-8", errors="ignore")[-4000:], re.M)
                    if reasons:
                        raise ValueError(reasons[-1].strip())
                    raise subprocess.CalledProcessError(process.returncode, command)
        if kind == "detect":
            artifact = json.loads((directory / "report.json").read_text(encoding="utf-8"))
            expected = {'gend', 'ucf', 'recce', 'f3net', 'npr', 'temporal_static'}
            if {item['id'] for item in artifact['methods']} != expected or 'summary' not in artifact:
                raise RuntimeError("检测报告未包含全部六种本地方法及汇总结论")
            if inputs.get("use_truthscan") and inputs.get("media_kind") == "video":
                try:
                    def cloud_progress(progress, message):
                        with lock:
                            jobs[identifier].update(progress=progress, message=message)
                    artifact["methods"].append(truthscan.detect(inputs["media"], cloud_progress))
                    completed = [item for item in artifact["methods"] if item.get("decision") in {"pass", "fail"}]
                    failed = sum(item["decision"] == "fail" for item in completed)
                    passed = sum(item["decision"] == "pass" for item in completed)
                    remote = artifact["methods"][-1]
                    artifact["summary"] = {"total": len(artifact["methods"]), "completed": len(completed),
                                           "passed": passed, "failed": failed,
                                           "uncertain": len(artifact["methods"]) - len(completed)}
                    # TruthScan is an independent cross-check. A high remote ML
                    # score raises the aggregate, while local evidence remains visible.
                    artifact["ai_probability"] = max(artifact["ai_probability"], remote["ai_probability"])
                    artifact["real_probability"] = 1.0 - artifact["ai_probability"]
                    artifact["confidence"] = max(artifact["ai_probability"], artifact["real_probability"])
                    if remote["decision"] == "fail":
                        artifact["verdict"] = "AI 生成倾向"
                    artifact["reason"] = f"{len(completed)} 项方法完成判断：{passed} 项通过、{failed} 项未通过。"
                except Exception as cloud_error:
                    artifact["methods"].append({
                        "id":"truthscan", "name":"TruthScan Generic", "status":"insufficient",
                        "verdict":"云端复核未完成", "decision":"uncertain", "score":None,
                        "ai_probability":None, "real_probability":None, "confidence":None,
                        "principle":"使用 TruthScan 的通用视频机器学习模型进行独立云端复核。",
                        "evidence":{"area":"整段视频", "high":[], "low":[],
                                    "explanation":str(cloud_error)[:180]},
                    })
                    artifact["summary"]["total"] += 1
                    artifact["summary"]["uncertain"] += 1
                (directory / "report.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            output = directory / ("output.wav" if kind == "voice" else "output.mp4")
            if not output.is_file() or not output.stat().st_size:
                raise RuntimeError("模型没有生成输出文件")
            artifact = publish(output, "audio" if kind == "voice" else "video")
            if kind == "voice":
                artifact["source_text"] = inputs["text"]
            if kind == "video":
                artifact["model"] = video_model
                artifact["scene"] = "original"
                artifact["presentation"] = video_profile(video_model)["presentation"]
        elapsed = round(time.monotonic() - started, 1)
        with lock:
            jobs[identifier].update(status="done", progress=100, message="已完成", result=artifact,
                                    elapsed_seconds=elapsed)
    except Exception as error:
        with lock:
            jobs[identifier].update(status="failed", message=f"处理失败：{error}。详细原因见本地任务日志。")
    (directory / "job.json").write_text(json.dumps(jobs[identifier], ensure_ascii=False), encoding="utf-8")


def progress_from_log(kind, output, video_model="sadtalker"):
    if kind == "voice":
        samples = re.findall(r"Sampling:\s*(\d+)%", output)
        return min(95, 18 + int(samples[-1]) * 77 // 100) if samples else 10
    if kind == "video":
        if video_model == "joyvasa":
            matches = re.findall(r"(\d+)%\|[^\n]*?\|(\s*\d+)/(\d+)", output)
            if matches:
                return min(94, 25 + int(matches[-1][0]) * 69 // 100)
            return 5
        if video_model == "echomimic_v3_flash":
            matches = re.findall(r"(\d+)%\|[^\n]*?\|(\s*\d+)/(\d+)", output)
            return min(94, 22 + int(matches[-1][0]) * 72 // 100) if matches else (18 if "Enable TeaCache" in output else 6)
        if video_model == "echomimic_v1":
            steps = re.findall(r"(\d+)%\|[^\n]*?\|(\s*\d+)/(\d+)", output)
            if steps:
                percent = int(steps[-1][0])
                return min(92, 20 + percent * 72 // 100)
            if "audio_fea_final" in output:
                return 18
            return 6
        render = re.findall(r"Face Renderer::?\s*(\d+)%", output)
        if render:
            return min(95, 42 + int(render[-1]) * 53 // 100)
        if "3DMM Extraction" in output:
            return 20
        return 8
    detector = re.findall(r"DETECTOR_PROGRESS\s+(\d+)", output)
    return int(detector[-1]) if detector else 5


def progress_message(kind, progress, video_model="sadtalker"):
    if kind == "voice":
        return "正在合成语音" if progress >= 18 else "正在准备语音模型"
    if kind == "video":
        if video_model == "joyvasa":
            if progress >= 25:
                return "JoyVASA 正在生成人脸、表情与头部动作"
            return "JoyVASA 正在加载模型"
        if video_model == "echomimic_v3_flash":
            return "EchoMimic V3 正在扩散渲染" if progress >= 22 else "EchoMimic V3 正在分段加载模型"
        if video_model == "echomimic_v1":
            return "EchoMimic V1 正在扩散渲染" if progress >= 20 else "EchoMimic V1 正在加载模型"
        return "正在渲染人像视频" if progress >= 42 else "正在分析人像与语音"
    return "正在运行本地检测方法" if progress >= 20 else "正在抽取人脸帧"


@app.get("/jobs/{identifier}")
def job_status(identifier: str):
    folder(identifier)
    with lock:
        if identifier in jobs:
            return jobs[identifier].copy()
    path = folder(identifier) / "job.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raise HTTPException(404, "任务不存在或服务已重启，请重新提交")
