# 部署指南

[中文](SETUP.md) · [English](SETUP.en.md) · [返回首页](../../README.md)

按你想用到哪一步来装，不用一次装完。

| 想用的功能 | 需要 | 看哪一节 |
|---|---|---|
| 只看界面 | Node.js 22.13+ | [A](#a-只看界面) |
| 爬取 + 规则分析 | 上一行 + Python 3.10+、Chrome/Edge 或 Chromium | [B](#b-爬取与规则分析) |
| 语音、视频、检测、模型分析 | 上一行 + WSL2 Ubuntu 22.04、NVIDIA GPU | [C](#c-完整本地推理) |
| 云端人像 / 云端复核 | 上一行 + 自己的腾讯 TokenHub、COS 或 TruthScan 账号 | [D](#d-可选的云端接口) |

所有脚本都从自身位置推导项目路径，项目可以放在任意目录。

## A. 只看界面

```powershell
git clone https://github.com/yxriam/talking-head-lab.git
cd talking-head-lab/web
npm ci
npm run dev -- --host 127.0.0.1 --port 3100
```

打开 <http://localhost:3100/studio>。没有后端时四个页面都能浏览，提交任务会提示服务未连接。

## B. 爬取与规则分析

在项目根目录：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File scripts\start-collector.ps1
```

`setup.ps1` 创建 `collector\.venv`、安装采集依赖和 Playwright 浏览器，并在缺少时安装前端依赖。然后按 A 启动界面，在“爬取信息”页点击“打开 Facebook 登录窗口”手动登录一次，登录状态保存在本机的 `collector\facebook-browser\`。

没有推理服务时，账号分析使用规则草稿，并在报告里注明没有调用模型的原因。

从旧目录迁移时，加上 `-MigrateFrom <旧项目目录>` 可以把已保存的登录状态和采集历史复制过来（不删除旧文件）。

## C. 完整本地推理

模型运行在 WSL 里：权重在 `/opt/media-models`，运行代码在 `/opt/media-app/local-media`（由部署脚本从 `inference/` 同步，不在 WSL 里执行 git）。

**首次安装**（每步体积大，逐个执行并看 `logs\` 下的日志）：

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

本地 Qwen（账号分析）和 EchoMimic V3、JoyVASA 的安装脚本是 `inference/install/install-scene-llm.sh` 与 `install-sota-generators.sh`，在 WSL 里以 root 运行；其中的 CUDA 编译参数需要与你的显卡匹配。安装脚本在一台机器上验证过，换机器前请先读一遍脚本。

**日常**：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1              # 启动采集、WSL 后端、界面并打开浏览器
powershell -ExecutionPolicy Bypass -File scripts\stop.ps1               # 停止界面和采集；加 -IncludeBackend 同时停后端
powershell -ExecutionPolicy Bypass -File scripts\deploy-inference.ps1   # 改了 inference/ 之后：同步、重启、检查健康
```

健康检查：

```powershell
curl.exe http://localhost:3100/api/health      # 各模型的 ready 状态
curl.exe http://127.0.0.1:8003/crawl/health    # 采集服务与登录状态
```

## D. 可选的云端接口

| 接口 | 用途 | 配置文件（在 WSL 里） | 启用脚本 |
|---|---|---|---|
| 腾讯 TokenHub YT HumanActor | 云端人像视频 | `/etc/media-app/tokenhub.env`，模板 `inference/config/tokenhub.env.example` | `/opt/media-app/local-media/configure-tokenhub-service.sh` |
| TruthScan | 云端检测复核 | `/etc/media-app/truthscan.env`，模板 `inference/config/truthscan.env.example` | `/opt/media-app/local-media/configure-truthscan-service.sh` |

两者都会把素材上传到对应服务并消耗你的账户额度，只有在界面里主动选择时才会调用。HumanActor 通过你自己的 COS 存储桶中转图片和音频，任务结束后删除临时对象。密钥只放在上述文件里，不进仓库。

## 使用

1. **爬取**：粘贴链接 → 开始采集 → 预览文字和素材 → 导出 ZIP。私人账号会自动给出分析，其他类型只显示分类说明。
2. **音色克隆**：上传已获授权的参考声音 → 输入台词 → 生成 → “用这段语音生成人像视频”。
3. **人像视频**：选择正脸照片、驱动语音和模型 → 生成 → “检测这个视频”。
4. **检测**：复用刚生成的视频，或上传任意图片、视频 → 查看每个方法的结论和时间段。

可以从任何一步开始。步骤之间用资源 ID 交接，不需要下载再上传。单文件上限 500 MB，GPU 任务逐个执行。

## 遇到问题

逐步安装说明、日志位置和常见错误见 [详细安装与排障](TROUBLESHOOTING.zh-CN.md)。
