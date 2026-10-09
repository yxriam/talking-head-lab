# 部署与使用详解

[中文](SETUP.md) · [English](SETUP.en.md) · [返回首页](../../README.md)

仅前端预览不需要GPU；声音/视频/检测需对应模型服务。先完成下面安装再日常启动。公共页面使用[仅采集示例](../showcase/facebook-trump/EXAMPLE.md)，当前发布版的自动私人门控仍待单独验收。

## 部署

### 环境与两种启动方式

| 组件 | 所需环境 |
|---|---|
| 仅浏览界面 | Node.js **>=22.13.0**，以[前端 package.json](../../facebook-scam/video-forensics-web/package.json)为准 |
| Windows 采集 | Python 3.10+、Playwright；已有 Chrome/Edge 可复用，否则安装 Chromium |
| 完整本地推理 | Windows + WSL2 / Ubuntu 22.04，NVIDIA GPU，模型独立环境及权重 |
| 维护目录 | WSL 模型 `/opt/media-models`；后端运行代码 `/opt/media-app/local-media` |
| 可选云端 | TokenHub + COS；TruthScan 配置独立启用 |

本轮实际验证了发布 checkout 的 `npm ci`、前端构建和上述合成素材任务。全新机器的完整 GPU 安装未在本轮重跑；当前安装脚本包含固定路径、Python 3.10 目录与 CUDA 编译参数，安装前需要按设备核对。

### A. 先运行界面预览

在一个新目录克隆并启动前端：

```powershell
git clone https://github.com/yxriam/talking-head-lab.git
Set-Location talking-head-lab/facebook-scam/video-forensics-web
npm ci
npm run dev -- --host 127.0.0.1 --port 3100
```

打开 **http://localhost:3100/studio**。没有后端与模型时，可以查看四个界面，生成和检测会显示未就绪状态。需要本地模型功能时继续下面的配置。

### B. 配置完整 Windows + WSL 环境

**1. 核对路径。**现有 Linux 安装/同步脚本仍引用 `D:/project/cv` 与 `D:/project/NZ/cv`。全新机器可以采用以下目录布局；已有 checkout 换路径时，先调整 `prepare-linux.ps1`、`run-linux.ps1`、`activate-api.sh`、`sync-runtime.sh` 和安装脚本中的对应路径。维护者当前发布 checkout 位于 `D:/project/facebook/talking-head-lab`，更新运行代码时同样要核对实际源目录。

<details>
<summary>全新机器的固定路径示例（仅在目录尚不存在时使用）</summary>

```powershell
New-Item -ItemType Directory -Path D:\project\NZ -Force
git clone https://github.com/yxriam/talking-head-lab.git D:\project\NZ\cv
New-Item -ItemType Junction -Path D:\project\cv -Target D:\project\NZ\cv
Set-Location D:\project\cv
```

</details>

**2. 安装 Windows 采集依赖与前端依赖。**在项目根目录执行：

```powershell
py -3 -m venv local-media\.venv
local-media\.venv\Scripts\python.exe -m pip install -r local-media\requirements-crawl.txt
local-media\.venv\Scripts\python.exe -m playwright install chromium
Set-Location facebook-scam/video-forensics-web
npm ci
npm run build
Set-Location ../..
```

低内存或正在进行模型任务时，先结束大任务；本轮构建用 `$env:RAYON_NUM_THREADS='2'` 限制原生构建线程后通过。浏览器使用默认检测到的 Chrome/Edge，或 Playwright Chromium。

**3. 准备 WSL 和模型。**安装 Ubuntu、完成其首次用户设置，然后检查 `nvidia-smi`：

```powershell
wsl --install -d Ubuntu-22.04
wsl -d Ubuntu-22.04 -- nvidia-smi
powershell -ExecutionPolicy Bypass -File .\local-media\prepare-linux.ps1
```

下面是已有安装脚本的依赖顺序。模型体积大，逐个执行并核对各步日志。`install-scene-llm.sh` 中的 CUDA 架构 `120` 等编译参数需与自己的设备匹配。

<details>
<summary>本地模型及后端服务安装顺序</summary>

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

当前 `sync-runtime.sh` 会检查所列模型目录，因此完整启动路径需要先准备这些目录。权重就绪、模型语义验收和服务验证分别记录；完整过程、日志、网络修复与停止方法见[安装和启动详解](../../网站启动说明.md)。

</details>

**4. 日常启动与健康检查。**模型环境和服务已准备后，在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\start-local.ps1
curl.exe http://localhost:3100/api/health
curl.exe http://127.0.0.1:8003/crawl/health
```

模型健康地址应返回 `status: ok`，各能力的 `ready` 表示当前配置状态。页面在 `http://localhost:3100/studio`；采集由 Windows 8003 提供，推理由 WSL 8002 提供，前端代理这两条链路。关闭浏览器会保留后台服务，完整停止方式见[启动详解](../../网站启动说明.md#3-怎么正确停止)。

### 可选：腾讯人像生成与云端复核

腾讯 TokenHub 使用 `yt-video-humanactor`，API Key 和 COS 的 SecretId、SecretKey、地域、存储桶写到 Ubuntu 的 `/etc/media-app/tokenhub.env`，通过现有 systemd 配置脚本加载。图片和音频上传 COS，使用短时签名 `image_url` / `audio_url` 提交，轮询完成后下载视频，程序尝试清理临时对象。

TruthScan 使用 `/etc/media-app/truthscan.env`。勾选云端复核会上传视频并使用账户额度；本轮演示已取消该勾选，仅执行本地方法。详细配置见[后端说明](../../local-media/README.md#tokenhub-人像驱动)与[云端复核说明](../../local-media/README.md#truthscan-免费云端复核)。真实配置、会话与密钥保留本机。

## 使用

1. **采集**：打开“爬取信息”→手动登录→粘贴可访问链接→开始采集→预览原文和素材→先确认用途，仅私人账号检查账号提醒，其他材料跳过风险分析→导出 ZIP。
2. **声音**：上传清晰、已授权的参考声音→输入台词→生成并试听→点击“用这段语音生成人像视频”。
3. **视频**：选择清晰正脸→选择驱动声音和模型→生成→预览/下载→点击“检测这个视频”。
4. **检测**：复用刚生成的视频或上传独立图片/视频→选择是否进行外部复核→查看汇总、方法解释和对应帧/秒数。

可以从任何模块开始。语音/视频交接复用资源 ID，不需要反复下载上传；直接上传的驱动音频只用于驱动，不自动转写，也不触发背景流程。当前 API 单文件上限 500 MB，GPU任务顺序执行。上传和生成文件保存在运行服务的 `data/`，由使用者按任务清理。
