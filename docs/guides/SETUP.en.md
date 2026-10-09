# Setup guide

[中文](SETUP.md) · [English](SETUP.en.md) · [Back to README](../../README.en.md)

Install only as far as the features you want.

| Features you want | You need | Section |
|---|---|---|
| Interface only | Node.js 22.13+ | [A](#a-interface-only) |
| Collection + rule-based analysis | The above + Python 3.10+, Chrome/Edge or Chromium | [B](#b-collection-and-rule-based-analysis) |
| Voice, video, detection, model-written analysis | The above + WSL2 Ubuntu 22.04, NVIDIA GPU | [C](#c-full-local-inference) |
| Cloud portrait model / cloud review | The above + your own Tencent TokenHub, COS or TruthScan account | [D](#d-optional-cloud-services) |

Every script derives the project path from its own location, so the project can live in any folder.

## A. Interface only

```powershell
git clone https://github.com/yxriam/talking-head-lab.git
cd talking-head-lab/web
npm ci
npm run dev -- --host 127.0.0.1 --port 3100
```

Open <http://localhost:3100/studio>. Without a back end all four pages can be browsed; submitting a job reports that the service is not connected.

## B. Collection and rule-based analysis

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File scripts\start-collector.ps1
```

`setup.ps1` creates `collector\.venv`, installs the collector dependencies and the Playwright browser, and installs the web dependencies if they are missing. Then start the interface as in A, open the Collect page and click the Facebook sign-in button once. The session is stored locally in `collector\facebook-browser\`.

Without the inference service, account analysis uses the rule draft and the report states why the model was not called.

When moving from an older layout, add `-MigrateFrom <old project folder>` to copy the saved session and collection history (the old files are not deleted).

## C. Full local inference

Models run inside WSL: weights in `/opt/media-models`, runtime code in `/opt/media-app/local-media` (copied from `inference/` by the deploy script; git is never run inside WSL).

**First installation** (each step is large; run them one at a time and check the logs under `logs\`):

```powershell
wsl --install -d Ubuntu-22.04
wsl -d Ubuntu-22.04 -- nvidia-smi
powershell -ExecutionPolicy Bypass -File inference\install\prepare-linux.ps1
powershell -ExecutionPolicy Bypass -File inference\install\run-linux.ps1 -Task setup-models
powershell -ExecutionPolicy Bypass -File inference\install\run-linux.ps1 -Task install-generators
powershell -ExecutionPolicy Bypass -File inference\install\run-linux.ps1 -Task install-echomimic
powershell -ExecutionPolicy Bypass -File inference\install\run-linux.ps1 -Task install-detectors
powershell -ExecutionPolicy Bypass -File inference\install\run-linux.ps1 -Task install-npr
powershell -ExecutionPolicy Bypass -File inference\install\run-linux.ps1 -Task install-gend
powershell -ExecutionPolicy Bypass -File inference\install\run-linux.ps1 -Task activate-api
```

The installers for the local Qwen model (account analysis) and for EchoMimic V3 and JoyVASA are `inference/install/install-scene-llm.sh` and `install-sota-generators.sh`; run them as root inside WSL. Their CUDA build flags must match your GPU. The installers were verified on one machine, so read them before using them on another.

**Daily use**:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1              # start collector, WSL back end and interface; open the browser
powershell -ExecutionPolicy Bypass -File scripts\stop.ps1               # stop interface and collector; add -IncludeBackend to stop the back end too
powershell -ExecutionPolicy Bypass -File scripts\deploy-inference.ps1   # after changing inference/: sync, restart, check health
```

Health checks:

```powershell
curl.exe http://localhost:3100/api/health      # ready state of every model
curl.exe http://127.0.0.1:8003/crawl/health    # collector and session state
```

## D. Optional cloud services

| Service | Purpose | Configuration file (inside WSL) | Enable script |
|---|---|---|---|
| Tencent TokenHub YT HumanActor | Cloud portrait video | `/etc/media-app/tokenhub.env`, template `inference/config/tokenhub.env.example` | `/opt/media-app/local-media/configure-tokenhub-service.sh` |
| TruthScan | Cloud detection review | `/etc/media-app/truthscan.env`, template `inference/config/truthscan.env.example` | `/opt/media-app/local-media/configure-truthscan-service.sh` |

Both upload your media to the service and use your account quota. They are called only when you select them in the interface. HumanActor passes the image and audio through your own COS bucket and deletes the temporary objects when the job ends. Keys live only in the files above, never in the repository.

## Using the workbench

1. **Collect**: paste a link → start → preview text and media → export ZIP. Private accounts get an analysis automatically; other types only show the classification note.
2. **Voice clone**: upload a reference voice you are authorised to use → enter the script → generate → "use this voice for a portrait video".
3. **Portrait video**: choose a frontal photo, the driving audio and a model → generate → "detect this video".
4. **Detect**: reuse the video you just generated or upload any image or video → read each method's verdict and time ranges.

You can start from any step. Steps hand over by resource id, so nothing has to be downloaded and uploaded again. Files are limited to 500 MB and GPU jobs run one at a time.

## Troubleshooting

Step-by-step installation notes, log locations and common errors are in the [detailed installation and troubleshooting guide](TROUBLESHOOTING.zh-CN.md) (Chinese).
