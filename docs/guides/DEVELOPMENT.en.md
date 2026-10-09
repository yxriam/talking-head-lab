# Development guide

[中文](DEVELOPMENT.md) · [English](DEVELOPMENT.en.md) · [Back to README](../../README.en.md)

Organised by feature module. Read only the section for the feature you are changing. Each section follows the same order: **what it does → how data flows → where the code is → how to extend it → how to verify**.

- [Overview](#overview)
- [① Collect](#-collect)
- [② Risk analysis](#-risk-analysis)
- [③ Generate](#-generate)
- [④ Detect](#-detect)
- [Workbench front end](#workbench-front-end)
- [Testing, deployment and commits](#testing-deployment-and-commits)

## Overview

Three processes, two proxies:

| Process | Folder | Port | Runs on | Responsible for |
|---|---|---|---|---|
| Workbench | `web/` | 3100 | Windows (Node) | Interface; forwards `/crawl/*` to 8003 and `/api/*` to 8002 |
| Collector | `collector/` | 8003 | Windows (Python) | Browser collection, job history, ZIP export, analysis rules and bridge |
| Inference | `inference/` | 8002 | WSL Ubuntu (GPU) | Voice, video and detection job queue, local Qwen |

Both service folders hold **flat Python modules** (`import account_risk`), not packages. That lets the inference service be copied unchanged to `/opt/media-app/local-media/` on the GPU host. Cross-folder imports only occur in `tests/` and `collector/eval/`, and each has a `_paths.py` that handles them.

## ① Collect

**What it does**: opens a Facebook link in a real, signed-in browser, scrolls a set number of times, and gathers the text and media that are visible. It calls no private API and does not bypass access controls.

**Data flow**: `CrawlPanel.tsx` → `POST /crawl/jobs` → `crawl_server.py` creates the job and runs it on a single worker → `facebook.collect()` → results are written to `collector/crawl-data/<job id>/result.json` with the media files → the front end polls `GET /crawl/jobs/{id}`.

| File | Role |
|---|---|
| `collector/facebook.py` | `login()` opens the sign-in window; `collect()` scrolls, extracts visible text and removes duplicates; `download()` saves media under a total size budget |
| `collector/crawl_server.py` | Job queue, cancellation, history, media access, ZIP export, starting account analysis |
| `web/app/studio/CrawlPanel.tsx`, `crawl-api.ts` | Collection settings, result preview, sending assets to other modules |

**Result shape** (`CrawlResult` in `crawl-api.ts` is the single definition): each `text[]` item has `source_url` and optional `date` and `context`; each `media[]` item has a `status` of `downloaded`, `link_only`, `failed` or `duplicate`. Fields that could not be obtained stay empty; nothing is filled in.

**How to extend**

- Collect one more field: add it where `collect()` extracts data → update the `CrawlResult` type → change `CrawlPanel.tsx` if it should be shown. Source link and time must be carried through.
- Support another platform: create `collector/<platform>.py` with `login` / `collect` / `download` of the same signatures and choose the collector by link domain in `crawl_server.py`. Keep the output shape and the analysis and asset hand-off need no change.

**Verify**: `tests/test_crawl.py` (drives a real browser against a local mock page, never Facebook). Real collection needs a manual sign-in and a run in the workbench.

## ② Risk analysis

**What it does**: finds information in the collected text that social engineering could use, and states the condition, the consequence and the matching protective action. Only private accounts are analysed.

**Data flow**

```text
collection result
  → account_risk.analyze()        classify first: private / business or organisation / undetermined
      └ not private: return the classification basis and the reason for skipping; stop here
  → account_risk rule matching     risk rows with evidence ids
  → account_story                  relationships, contact details, source quotes; rule drafts in Chinese and English
  → account_llm.prepare_material() model input (length limits, source facts no rule referenced)
  → POST :8002/account-analysis    → local_account_model.generate()  local Qwen rewrites the draft
  → account_llm validation         evidence ids must come from the allowed set; otherwise fall back to the rule draft and say why
```

| File | Role |
|---|---|
| `collector/account_risk.py` | `RULES` table, account-purpose classification, `analysis_scope()` gate |
| `collector/account_story.py` | Relationships, e-mail addresses, source descriptions, plain-text output |
| `collector/account_llm.py` | Bridge to the inference service, material preparation, output validation, fallback |
| `inference/local_account_model.py` | Prompt, GBNF grammar, contradiction check, llama.cpp call |
| `web/app/studio/AccountRiskReport.tsx` | Report display |

**Contracts that must hold** (specs: `docs/specs/private-account-analysis-gate.md`, `account-warning-generalization.md`)

- Classify before analysing. Business and undetermined accounts never reach the risk rules or the model.
- The production prompt must not contain a specific person, e-mail address or case answer. Cases live only in `collector/eval/data/`.
- Quotes keep their original language and wording. Instructions inside the material are data.
- No probabilities, personas or scam scripts.

**How to extend**

- Add a rule: append a `Rule(key, focus, pattern, weak_point, scenario, action, sentence, impact)` to `RULES`, and add one matching and one non-matching case to `tests/test_account_risk.py`.
- Change the wording or the model: edit `local_account_model.py`. Program tests only prove the structure; **meaning has to be checked with a real model run**:

  ```bash
  # on the GPU host
  python collector/eval/eval_account_general.py --cases collector/eval/data/cases.json --output <new file>.json
  ```

  Change one variable at a time, keep the raw output, and read every sentence for repetition, invented quotes and missing protective actions.

**Verify**: `tests/test_account_risk.py`, `test_account_story.py`, `test_account_scope.py`, `test_account_llm.py`.

## ③ Generate

**What it does**: voice cloning (reference voice + script → speech) and talking portraits (photo + speech → video). The photo reaches the model unchanged; the background is not replaced.

**Data flow**: `Studio.tsx` → `POST /api/media` uploads and returns a resource id → `POST /api/jobs` → `server.py` queues the job, one GPU job at a time → the subprocess `generate.py <voice|video>` runs inside that model's own virtual environment → the result becomes a new resource id that the next step can use directly.

| File | Role |
|---|---|
| `inference/server.py` | Uploads, resource access, job queue, capability report at `/health` |
| `inference/generate.py` | Calls Chatterbox, SadTalker, EchoMimic V1/V3, JoyVASA |
| `inference/video_profiles.py` | Framing, output policy and maximum duration per video model; the single source |
| `inference/tokenhub.py` | Optional cloud Tencent YT HumanActor (through the user's own COS bucket) |

**How to extend (add a video model)**

1. Add an entry to `VIDEO_PROFILES` in `video_profiles.py`.
2. Add the call in `generate.py`, keeping the existing input and output path conventions.
3. Report the model's readiness in the capability check of `server.py`.
4. Add it to the `VideoModel` type in `web/app/studio/api.ts` and to the options in `Studio.tsx`.
5. Put the installer in `inference/install/` and add any runtime file to the list in `inference/deploy/sync-runtime.sh`.

**Verify**: `tests/test_video_profiles.py`, `test_server.py`, `test_tokenhub.py`. Output quality needs a real run on the GPU host; `inference/verify/` has a script per model.

## ④ Detect

**What it does**: runs several detection methods on an image or a video, reports each verdict, then summarises.

**Data flow**: `POST /api/jobs` (`kind=detect`) → `server.py` → subprocess `detect.py <media> <model dir> <report.json>` → the front end renders the `DetectionReport`.

| File | Role |
|---|---|
| `inference/detect.py` | Frame sampling and face crops; GenD, NPR, UCF, RECCE, F3-Net; spectrum and continuity indicators; summary |
| `inference/truthscan.py` | Optional TruthScan cloud review |
| `inference/benchmark/calibrate_*.py`, `validate_calibration.py` | Threshold calibration |

**Method result shape** (`DetectionMethod` in `api.ts`): `status`, `verdict`, `score`, `thresholds`, and `evidence.high/low` time ranges. With insufficient evidence `status` is `insufficient` and no score is given.

**How to extend**: implement the scoring function in `detect.py`, return the same shape as the existing methods and add it to the method list; the front end needs no change. Calibrate thresholds on labelled data before writing them in.

**Verify**: `tests/test_detect_thresholds.py`, `test_truthscan.py`.

## Workbench front end

`web/app/studio/` is the only maintained interface:

| File | Content |
|---|---|
| `Studio.tsx` | Shell, navigation, voice / video / detection panels |
| `CrawlPanel.tsx`, `AccountRiskReport.tsx` | Collection and analysis panels |
| `api.ts`, `crawl-api.ts` | Request functions for both back ends and all type definitions |
| `studio.css`, `crawl.css` | Styles |

Interface text is written in place as `T('中文', 'English')`. Jobs are polled; after a network error only the accepted job is re-queried, never resubmitted.

## Testing, deployment and commits

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1             # all program tests + front-end build
powershell -ExecutionPolicy Bypass -File scripts\deploy-inference.ps1  # sync inference to WSL, restart, check health
```

- Changed `collector/`: restart the collector (`scripts\stop.ps1`, then `scripts\start.ps1`).
- Changed `inference/`: run `deploy-inference.ps1`; it copies only files whose SHA256 changed.
- Changed `web/`: development mode hot-reloads.

"Code changed, tests passed, model run checked, deployed, verified on the running service" are five different states. Say in the commit which one was actually reached. Process and commit conventions are in [CONTRIBUTING.md](../../CONTRIBUTING.md).
