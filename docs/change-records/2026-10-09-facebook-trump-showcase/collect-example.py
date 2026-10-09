"""Bounded showcase run of the project's sole Facebook collector; no risk model."""
import hashlib
import importlib.util
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

ROOT = Path(__file__).resolve().parents[3]
RECORD = Path(__file__).resolve().parent
SOURCE = ROOT / "facebook-scam/crawler/facebook.py"
spec = importlib.util.spec_from_file_location("facebook_collector", SOURCE)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
identifier = uuid.uuid4().hex
work = ROOT / "local-media/crawl-data" / identifier
work.mkdir(parents=True)
options = {"url": "https://www.facebook.com/DonaldTrump/", "max_scrolls": 4,
           "max_images": 4, "max_videos": 1, "download_media": True}
job = {"id": identifier, "kind": "crawl", "status": "running", "stage": "queued",
       "progress": 0, "message": "", "counts": {}, "source_url": options["url"],
       "created_at": datetime.now(timezone.utc).isoformat(),
       "runner": "direct call to existing collector.collect; account analysis omitted"}
receipt = {"job_id": identifier, "options": options, "created_at": job["created_at"],
           "collector_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           "raw_data": str(work), "account_model_called": False}

def update(**fields):
    if "counts" in fields:
        fields["counts"] = {**job["counts"], **fields["counts"]}
    job.update(fields)
    (work / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: job[k] for k in ("status", "stage", "progress", "counts")}), flush=True)

open_context = collector.open_context
collector.open_context = lambda playwright, profile: open_context(playwright, profile, headless=True)
started = time.monotonic()
try:
    result = collector.collect(options, ROOT / "local-media/facebook-browser", work, Event(), update)
    (work / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "text.txt").write_text("\n\n".join(item["text"] for item in result["text"]), encoding="utf-8")
    # Use the existing job-file schema for local UI preview/export; never call analysis.
    public_result = {**result, "media": [dict(asset) for asset in result["media"]]}
    for asset in public_result["media"]:
        if asset.get("status") == "downloaded":
            asset["url"] = f"/crawl/media/{identifier}/{asset['id']}"
        asset.pop("src", None)
    update(status="done", stage="done", progress=100, message="已完成", result=public_result)
except collector.LoginRequired as error:
    update(status="needs_login", stage="login", message=str(error))
except Exception as error:
    update(status="failed", stage="failed", message=f"{type(error).__name__}: {error}")
finally:
    job["elapsed_seconds"] = round(time.monotonic() - started, 1)
    receipt.update(status=job["status"], elapsed_seconds=job["elapsed_seconds"], message=job["message"], counts=job["counts"])
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    (work / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    serialized = json.dumps(receipt, ensure_ascii=False, indent=2)
    (work / "collection-receipt.json").write_text(serialized, encoding="utf-8")
    # Never overwrite the original committed acceptance evidence when someone reruns the example.
    if not (RECORD / "collection-receipt.json").exists():
        (RECORD / "collection-receipt.json").write_text(serialized, encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
sys.exit(0 if job["status"] == "done" else 2)
