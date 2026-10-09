"""Local Windows Facebook API. GPU inference stays in the Ubuntu server."""

import importlib.util
import json
import logging
import re
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
import account_risk
import account_llm

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("facebook_collector", ROOT / "facebook.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
DATA = ROOT / "crawl-data"
PROFILE = ROOT / "facebook-browser"
ID = re.compile(r"^[a-f0-9]{32}$")
TERMINAL = {"done", "failed", "cancelled", "needs_login"}
app = FastAPI(title="Facebook collector", docs_url=None, redoc_url=None)
pool = ThreadPoolExecutor(max_workers=1)
lock = Lock()
export_lock = Lock()
jobs, stops = {}, {}


@app.middleware("http")
async def local_only(request: Request, call_next):
    if request.url.hostname not in {"localhost", "127.0.0.1", "testserver"}:
        return JSONResponse({"detail": "只允许本地访问"}, status_code=403)
    if request.headers.get("origin") not in {None, "http://localhost:3100", "http://127.0.0.1:3100"}:
        return JSONResponse({"detail": "不允许此网页来源"}, status_code=403)
    return await call_next(request)


def directory(identifier):
    if not ID.fullmatch(identifier):
        raise HTTPException(404, "采集任务不存在")
    return DATA / identifier


def read_job(identifier):
    try:
        item = json.loads((directory(identifier) / "job.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        raise HTTPException(404, "采集任务不存在")
    if item["status"] not in TERMINAL:
        item.update(status="cancelled", message="服务已重启，采集任务已中断")
    return item


def persist(item):
    path = directory(item["id"]) / "job.json"
    temporary = path.with_suffix(".part")
    temporary.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


@app.get("/crawl/health")
def health():
    return {"status": "ok", "ready": importlib.util.find_spec("playwright") is not None,
            "session_saved": PROFILE.exists(), "browser": collector.browser_channel() or "chromium",
            "account_analysis": account_llm.status()}


class CrawlInput(BaseModel):
    url: str = Field(max_length=2048)
    max_scrolls: int = Field(default=8, ge=1, le=30)
    max_images: int = Field(default=24, ge=0, le=80)
    max_videos: int = Field(default=6, ge=0, le=20)
    download_media: bool = True

    @field_validator("url")
    @classmethod
    def valid_url(cls, value):
        return collector.facebook_url(value)


def submit(kind, options):
    if not health()["ready"]:
        raise HTTPException(503, "请先安装 requirements-crawl.txt 中的 Playwright 依赖")
    with lock:
        if any(item["status"] not in TERMINAL for item in jobs.values()):
            raise HTTPException(409, "已有采集或登录任务正在运行")
        identifier = uuid.uuid4().hex
        directory(identifier).mkdir(parents=True)
        item = {"id": identifier, "kind": kind, "status": "queued", "stage": "queued", "progress": 0,
                "message": "等待处理", "source_url": options.get("url", "https://www.facebook.com/"),
                "created_at": datetime.now(timezone.utc).isoformat(), "counts": {}}
        jobs[identifier], stops[identifier] = item, Event()
        persist(item)
        pool.submit(run_job, identifier, options)
        return item.copy()


@app.post("/crawl/jobs")
def create_job(options: CrawlInput):
    return submit("crawl", options.model_dump())


@app.post("/crawl/browser")
def open_login():
    return submit("login", {})


def run_job(identifier, options):
    started = time.monotonic()
    def update(**fields):
        with lock:
            jobs[identifier].update(fields)
            persist(jobs[identifier])
    update(status="running")
    try:
        work = directory(identifier)
        if jobs[identifier]["kind"] == "login":
            result = collector.login(PROFILE, stops[identifier], update)
        else:
            result = collector.collect(options, PROFILE, work, stops[identifier], update)
            for media in result["media"]:
                if media.get("status") == "downloaded":
                    media["url"] = f"/crawl/media/{identifier}/{media['id']}"
                media.pop("src", None)
            for entry in result["media"] + result["text"]:
                try:
                    entry["source_url"] = collector.facebook_url(entry.get("source_url", ""))
                except ValueError:
                    entry["source_url"] = result["source_url"]
            update(stage="analyzing", progress=97, message="正在整理账号反诈证据")
            result["analysis"] = account_risk.analyze(result)
            update(stage="analyzing", progress=98, message="正在调用本地 Qwen 生成账号防范分析")
            try:
                result["analysis"] = account_llm.rewrite(result["analysis"])
            except account_llm.ModelError as error:
                # Collection must survive inference failures; label the fallback.
                result["analysis"]['generation']['fallback_reason']=str(error)
                result['warnings'].append('本地 LLM 分析未完成，当前展示证据规则草稿：'+str(error))
            (work / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            (work / "text.txt").write_text("\n\n".join(item["text"] for item in result["text"]), encoding="utf-8")
        collector.check_cancel(stops[identifier])
        update(status="done", stage="done", progress=100, message="已完成", result=result,
               elapsed_seconds=round(time.monotonic() - started, 1))
    except collector.Cancelled:
        update(status="cancelled", stage="cancelled", message="已停止采集")
    except collector.LoginRequired as error:
        update(status="needs_login", stage="login", message=str(error))
    except Exception as error:
        logging.getLogger(__name__).exception("Facebook task %s failed", identifier)
        update(status="failed", stage="failed", message=f"采集失败：{type(error).__name__}。请确认浏览器可访问 Facebook。")
    finally:
        update(elapsed_seconds=round(time.monotonic() - started, 1))


@app.get("/crawl/jobs")
def history():
    paths = sorted(DATA.glob("*/job.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:50]
    with lock:
        items = [jobs.get(path.parent.name) or read_job(path.parent.name) for path in paths]
        return [{key: value for key, value in item.items() if key != "result"} for item in items]


@app.get("/crawl/jobs/{identifier}")
def job(identifier: str):
    directory(identifier)
    with lock:
        return jobs[identifier].copy() if identifier in jobs else read_job(identifier)


@app.post("/crawl/jobs/{identifier}/cancel")
def cancel(identifier: str):
    item = job(identifier)
    with lock:
        if item["status"] not in TERMINAL and identifier in stops:
            stops[identifier].set()
    return {"status": "requested"}


@app.post("/crawl/jobs/{identifier}/analyze")
def analyze_account(identifier: str):
    item = job(identifier)
    if item["kind"] != "crawl" or item["status"] != "done" or not item.get("result"):
        raise HTTPException(409, "采集完成后才能分析账号信息")
    try:
        analysis=account_llm.rewrite(account_risk.analyze(item['result']))
    except account_llm.ModelError as error:
        raise HTTPException(503,str(error)) from error
    result = {**item["result"], "analysis": analysis}
    work = directory(identifier)
    with export_lock:
        temporary = work / "result.part"
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(work / "result.json")
        (work / "export.zip").unlink(missing_ok=True)
        (work / "export-en.zip").unlink(missing_ok=True)
        with lock:
            item["result"] = result
            jobs[identifier] = item
            persist(item)
    return result["analysis"]


@app.get("/crawl/media/{identifier}/{asset_id}")
def media(identifier: str, asset_id: str):
    item = job(identifier)
    if not ID.fullmatch(asset_id):
        raise HTTPException(404, "素材不存在")
    asset = next((asset for asset in item.get("result", {}).get("media", []) if asset.get("id") == asset_id), None)
    if not asset or asset.get("status") != "downloaded":
        raise HTTPException(404, "素材未下载")
    filename = asset["filename"]
    if Path(filename).name != filename or "\\" in filename:
        raise HTTPException(404, "素材不存在")
    path = directory(identifier) / filename
    if not path.is_file():
        raise HTTPException(404, "素材不存在")
    return FileResponse(path, filename=filename, content_disposition_type="inline")


@app.get("/crawl/jobs/{identifier}/export")
def export(identifier: str, language: Literal['zh','en']='zh'):
    work = directory(identifier)
    archive = work / ("export-en.zip" if language=='en' else "export.zip")
    with export_lock:
        # Read the report under the same lock as refresh, so JSON and prose match.
        item = job(identifier)
        if item["kind"] != "crawl" or item["status"] != "done":
            raise HTTPException(409, "采集完成后才能导出")
        report = item['result'].get('analysis')
        conclusion = report.get('conclusion_en' if language=='en' else 'conclusion') if report else None
        if language=='en' and report and not conclusion:
            raise HTTPException(409, "Refresh analysis to generate the English report first.")
        if not archive.exists():
            temporary = archive.with_suffix('.part')
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for filename in ("result.json", "text.txt"):
                    bundle.write(work / filename, filename)
                if conclusion:
                    bundle.writestr('account-analysis.txt', conclusion)
                for asset in item["result"]["media"]:
                    if asset.get("status") == "downloaded":
                        bundle.write(work / asset["filename"], "media/" + asset["filename"])
            temporary.replace(archive)
    suffix='-en' if language=='en' else ''
    return FileResponse(archive, filename=f"facebook-{identifier[:8]}{suffix}.zip")
