# Project structure and development

[中文](DEVELOPMENT.md) · [English](DEVELOPMENT.en.md) · [Back to home](../../README.en.md)

## Project structure and code map

```text
talking-head-lab/
├─ README.md / README.en.md                 Chinese / English entry points
├─ facebook-scam/
│  ├─ crawler/facebook.py                   Sole online collector
│  └─ video-forensics-web/
│     ├─ app/studio/                        Four modules, styles, frontend APIs
│     ├─ build/sites-vite-plugin.ts         Required Vite plugin source
│     └─ tests/                             Existing frontend checks
├─ local-media/
│  ├─ crawl_server.py / server.py            Windows collection / WSL media API
│  ├─ account_risk.py / account_story.py      Text evidence rules and prose
│  ├─ account_llm.py / local_account_model.py Local bridge and inference
│  ├─ generate.py / video_profiles.py        Model subprocesses, layout, duration
│  ├─ local_scene.py / prepare_scene.py      Historical background experiments, outside video flow
│  ├─ detect.py                             Detection and supporting forensics
│  ├─ tokenhub.py / truthscan.py             Optional external adapters
│  ├─ detector-runtime/                     Detector registration installer source
│  └─ test_*.py / *.sh / *.ps1               Tests, install, startup, synchronization
├─ docs/guides/                            Setup / development guides
├─ docs/proposal/                          Research proposals
├─ docs/showcase/                           Synthetic generation / live collection examples
├─ docs/specs/ / docs/change-records/        Contracts, changes, verification, rollback
└─ AGENTS.md / CLAUDE.md / .cursor/rules/    Shared collaboration rules and entry points
```

Research proposals live in `docs/proposal/`; legacy demos retain their sources in the ignored local `archive/legacy-demos/`. Maintain the current workbench under `app/studio/`. Model weights, virtual environments, private media, complete collection data and real secrets are excluded from source control. Public examples and provenance live in `docs/showcase/`.

## Further development

### Where to make a change

| Change | Entry points and checks |
|---|---|
| UI, layout, frontend behavior | `Studio.tsx`, `CrawlPanel.tsx`, `studio.css`, `crawl.css`, `api.ts`; frontend build and behavior checks |
| Collection fields | `crawler/facebook.py` → `crawl_server.py` → account rules/bridge/output; retain sources and time metadata, run collection tests |
| Account prompts or prose | `account_risk.py` → `account_story.py` → `account_llm.py` → `server.py /account-analysis` → `local_account_model.py`; program tests and actual model acceptance |
| Another video model | `video_profiles.py`, `generate.py`, backend capabilities/queue, frontend choices; specify layout, duration, and failures |
| Detection method | `detect.py`, report fields, frontend presentation; retain actual thresholds, sampled times, and insufficient-evidence states |

### Verify, synchronize, and roll back

Read [AGENTS.md](../../AGENTS.md) and [PROJECT.md](../../PROJECT.md), then use the [maintenance workflow](../../docs/WORKFLOW.md) to freeze a task specification, inspect the actual diff, run directly relevant checks, and commit one accepted task at a time.

```powershell
local-media\.venv\Scripts\python.exe -m unittest discover -s local-media -p test_account_llm.py -v
local-media\.venv\Scripts\python.exe -m unittest discover -s local-media -p test_server.py -v
Set-Location facebook-scam/video-forensics-web
npm run build
```

Add account-rule/prose, collection, or model checks according to scope. Prompt changes require frozen cases and real model outputs; program tests do not replace semantic acceptance.

Backend deployment uses SHA256 synchronization through `sync-runtime.sh`, followed by restart and service verification. Its source path must point to the actual maintained checkout. Source commits, GitHub publication, and runtime deployment are separate stages.

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/sync-runtime.sh
wsl -d Ubuntu-22.04 -u root -- systemctl restart local-media.service
curl.exe http://localhost:3100/api/health
```

For a shared change, run `git revert <actual commit>`, verify it, and normally `git push origin main`. The [showcase change record](../../docs/change-records/2026-10-09-readme-showcase/记录.md) preserves this task's real inputs, timings, failures and fixes, checks, and rollback.
