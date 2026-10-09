# Deployment and usage guide

[中文](SETUP.md) · [English](SETUP.en.md) · [Back to home](../../README.en.md)

Interface preview requires no GPU; voice/video/detection require their model services. Install first, then use the daily startup command. For public pages use the [collection-only example](../showcase/facebook-trump/EXAMPLE.en.md); automatic personal-account gating in the published version still requires separate acceptance.

## Deployment

### Requirements and two startup paths

| Component | Environment |
|---|---|
| Interface preview | Node.js **>=22.13.0**, as declared in [package.json](../../facebook-scam/video-forensics-web/package.json) |
| Windows collection | Python 3.10+, Playwright; existing Chrome/Edge can be reused, otherwise install Chromium |
| Full local inference | Windows + WSL2 / Ubuntu 22.04, NVIDIA GPU, separate model environments and weights |
| Maintained directories | Models: `/opt/media-models`; backend runtime: `/opt/media-app/local-media` |
| Optional cloud features | TokenHub + COS; TruthScan is configured separately |

This task verified `npm ci`, the frontend build in the publishing checkout, and the synthetic-media runs above. A full GPU installation on a fresh machine was not repeated. The current installers contain fixed paths, Python 3.10 directory assumptions, and CUDA compilation settings that must be checked against the target device.

### A. Start with an interface preview

Clone into a new directory and start the frontend:

```powershell
git clone https://github.com/yxriam/talking-head-lab.git
Set-Location talking-head-lab/facebook-scam/video-forensics-web
npm ci
npm run dev -- --host 127.0.0.1 --port 3100
```

Open **http://localhost:3100/studio**. Without the backend and models, the four interfaces remain visible and generation/detection show unavailable capabilities. Continue below to enable local model execution.

### B. Configure the full Windows + WSL environment

**1. Check paths.** The Linux installation/synchronization scripts still reference `D:/project/cv` and `D:/project/NZ/cv`. A fresh machine can use the layout below. For another checkout location, first update corresponding paths in `prepare-linux.ps1`, `run-linux.ps1`, `activate-api.sh`, `sync-runtime.sh`, and installation scripts. The maintainer's publishing checkout is currently `D:/project/facebook/talking-head-lab`; runtime updates must likewise point to the actual source checkout.

<details>
<summary>Fixed-path example for a fresh machine, only when the directories do not already exist</summary>

```powershell
New-Item -ItemType Directory -Path D:\project\NZ -Force
git clone https://github.com/yxriam/talking-head-lab.git D:\project\NZ\cv
New-Item -ItemType Junction -Path D:\project\cv -Target D:\project\NZ\cv
Set-Location D:\project\cv
```

</details>

**2. Install Windows collector and frontend dependencies.** From the project root:

```powershell
py -3 -m venv local-media\.venv
local-media\.venv\Scripts\python.exe -m pip install -r local-media\requirements-crawl.txt
local-media\.venv\Scripts\python.exe -m playwright install chromium
Set-Location facebook-scam/video-forensics-web
npm ci
npm run build
Set-Location ../..
```

Finish large model jobs before building on a memory-constrained system. This task's build passed with native build threads limited using `$env:RAYON_NUM_THREADS='2'`. The collector selects installed Chrome/Edge, or falls back to Playwright Chromium.

**3. Prepare WSL and the models.** Install Ubuntu, complete its first-run user setup, and check GPU access:

```powershell
wsl --install -d Ubuntu-22.04
wsl -d Ubuntu-22.04 -- nvidia-smi
powershell -ExecutionPolicy Bypass -File .\local-media\prepare-linux.ps1
```

Below is the dependency order for the existing installers. Model downloads are large; run each step separately and check its logs. CUDA architecture `120` and other settings in `install-scene-llm.sh` must match the device.

<details>
<summary>Local model and backend service installation order</summary>

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task setup-models
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-generators
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-echomimic
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-detectors
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-npr
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task install-gend
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/install-scene-llm.sh
wsl -d Ubuntu-22.04 -u root -- mkdir -p /opt/media-app/local-media
wsl -d Ubuntu-22.04 -u root -- cp /mnt/d/project/cv/local-media/patch_echomimic_v3_memory.py /opt/media-app/local-media/
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/install-sota-generators.sh
powershell -ExecutionPolicy Bypass -File .\local-media\run-linux.ps1 -Task activate-api
```

`sync-runtime.sh` currently checks its listed model directories, so this full startup path requires those directories first. Weight readiness, model acceptance, and service verification are separate stages. The existing [detailed installation/startup guide in Chinese](../../网站启动说明.md) covers logs, network repairs, and shutdown.

</details>

**4. Daily startup and health checks.** Once model environments and the service are prepared, run from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\start-local.ps1
curl.exe http://localhost:3100/api/health
curl.exe http://127.0.0.1:8003/crawl/health
```

The model health endpoint should return `status: ok`; each capability's `ready` describes its current configuration. The workbench is at `http://localhost:3100/studio`. Windows provides collection on 8003, WSL provides inference on 8002, and the frontend proxies both. Closing the browser leaves background services running; the [shutdown section](../../网站启动说明.md#3-怎么正确停止) documents how to stop them completely.

### Optional: Tencent video generation and cloud cross-checks

Tencent TokenHub uses `yt-video-humanactor`. Put the API key and COS SecretId, SecretKey, region, and bucket in Ubuntu's `/etc/media-app/tokenhub.env`, loaded through the existing systemd configuration script. The adapter uploads both inputs to COS, submits short-lived signed `image_url` / `audio_url` links, polls the job, downloads the result, and attempts to clean up temporary objects.

TruthScan uses `/etc/media-app/truthscan.env`. Enabling its checkbox uploads the video and uses account quota. It was disabled for this demonstration, which ran only local methods. Configuration details are in the [backend TokenHub guide](../../local-media/README.md#tokenhub-人像驱动) and [TruthScan guide](../../local-media/README.md#truthscan-免费云端复核). Real credentials, sessions, and secrets stay on the local machine.

## Usage

1. **Collect**: open “Collect information” → log in manually → paste an accessible URL → collect → preview sources and media → confirm purpose and inspect suggestions only for a personal account, skipping risk analysis otherwise → export a ZIP.
2. **Voice**: upload clear, authorized reference speech → enter new text → generate and listen → choose “Create a portrait video with this voice.”
3. **Video**: select a clear front-facing portrait → choose audio and a model → generate → preview/download → choose “Detect this video.”
4. **Detect**: reuse the generated video or upload an independent image/video → decide whether to enable the external cross-check → review the summary, explanations, frames, and times.

Start from any module. Voice/video handoffs reuse resource IDs without repeated downloads and uploads. Directly uploaded driving audio is used for driving, without automatic transcription or a background stage. The current API file limit is 500 MB, and GPU work is serialized. Uploaded and generated files remain in the running service's `data/`, with task cleanup managed by the user.
