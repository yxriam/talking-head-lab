# 本地 AI 媒体服务

项目保持两个部分，沿用已有网页，不移动原始素材：

- `../facebook-scam/video-forensics-web/app/studio/`：语音、视频、分析与 Facebook 采集四页界面。
- 本目录：`server.py` 提供上传、文件播放、任务状态；`generate.py` 调用 Chatterbox、SadTalker、EchoMimic V1、JoyVASA 与 EchoMimic V3 Flash；`data/` 保存本地任务；模型放在 Linux 的 `/opt/media-models/`。

人像视频按模型能力选择构图，不统一拉伸或拼接。模型差异集中在
`video_profiles.py`；网页、肖像预处理和推理出口使用同一套选择。

| 模型 | 输入构图 | 输出策略 | 视觉取舍 |
| --- | --- | --- | --- |
| SadTalker | 方形头肩 | `extcrop` 后只裁掉编码补边 | 身份稳定，不回贴原始大图 |
| EchoMimic V1 | 512 方形 | 保留原生视频流 | 不重构画幅，最长 20 秒 |
| JoyVASA | 方形头肩 | 保留原生视频流 | 头部动作更明显，不二次裁剪 |
| EchoMimic V3 Flash | 384 方形 | 保留原生视频流 | 只做 4 秒完整短片，不分段拼接 |
| YT HumanActor | 竖版肖像 | 保留云端原生画幅 | 完整人物构图与自然动作 |

保留的处理只有三类：根据台词选择安静且合理的环境、保留原始人物像素、按模型真实能力选择构图。未加入人脸重绘、背景动画、统一放大、补帧、强制锐化和长片分段拼接；这些步骤在当前硬件与模型上会引入身份变化、接缝或时序跳变，不能稳定提升观感。

没有数据库、消息队列或远端服务。GPU任务单个执行，生成完成后的同一资源ID可直接用于下一步。历史脚本留在CV根目录，作为来源保留，不在新服务中使用远端地址。

## 日常启动

Facebook 采集由 Windows 的 `crawl_server.py` 与 `../facebook-scam/crawler/facebook.py` 执行。安装 `requirements-crawl.txt` 后，一键启动脚本也会启动 8003 采集服务；详情见 `../facebook-scam/README.md`。原 8002 模型服务不承担浏览器操作。

在 Windows PowerShell 中运行：

```powershell
Set-Location D:\project\NZ\cv
powershell -ExecutionPolicy Bypass -File .\local-media\start-local.ps1
```

脚本会保持 WSL 运行、启动 Ubuntu 后端、读取当前 WSL 地址、启动网页并打开浏览器。完整的首次配置、验证、停止和排错步骤见 [`../网站启动说明.md`](../网站启动说明.md)。GPU 推理要求 Linux 环境。

网页地址：`http://localhost:3100/studio`。Ubuntu API 地址：`http://127.0.0.1:8002`。仅允许本地及上述网页来源访问。

## TokenHub 人像驱动

网页的人像模型中可以选择 `YT HumanActor`。人像图片和驱动音频会临时上传到用户自己的腾讯 COS，再以短时签名 URL 提交，避免 Base64 大请求在跨境网络中写入超时；任务结束后两个临时文件都会立即删除。生成视频会下载回本地并沿用同一个资源 ID 进入检测。

Ubuntu 服务从 `/etc/media-app/tokenhub.env` 读取以下配置：

```dotenv
TOKENHUB_API_KEY=TokenHub控制台创建的API Key
TENCENT_COS_SECRET_ID=用于访问指定存储桶的SecretId
TENCENT_COS_SECRET_KEY=对应的SecretKey
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET=完整存储桶名（包含APPID）
```

请给 COS 凭据限定到这个存储桶；不要把真实密钥写入 Git 工作区。当前 TokenHub 兼容接口使用 `audio_url`、`image_base64`、`frame_rate`、`logo_add` 等 snake_case 参数。TokenHub 接口使用 720p、25 fps、关闭模型水印，音频限制为 2–60 秒。用户仍应仅处理已获授权的照片和声音。

## TruthScan 免费云端复核

检测页已接好 TruthScan Generic 视频接口。免费方案每月包含 30 秒，开关只在密钥配置完成后显示；勾选时视频会上传至 TruthScan。没有密钥、额度不足或接口异常时，本地检测仍会完成，并把云端方法标为“未完成”。

在 TruthScan 控制台创建 API key 后，将它写入 Ubuntu 的 `/etc/media-app/truthscan.env`，不要写入 Git 工作区：

```dotenv
TRUTHSCAN_API_KEY=你的密钥
```

再安装服务配置并重启：

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /opt/media-app/local-media/configure-truthscan-service.sh
```

当前已通过公开 `/health` 实测 WSL 网络可达，也通过无网络模拟验证上传、任务轮询、ML 概率解析和失败降级；按要求尚未提交样本，未消耗免费额度。

## 模型状态

Chatterbox、SadTalker、EchoMimic V1、JoyVASA、EchoMimic V3 Flash 及五个检测模型已在 RTX 5070 Ti 上部署并通过真实推理。JoyVASA 会同时驱动嘴型、表情和头部姿态；EchoMimic V3 Flash 使用 Transformer/VAE 驻留 GPU、T5/CLIP 按需卸载的混合模式，适合 4 秒以内的高质量短片。检测页还加入照片驱动时序静态性方法，并可选用 TruthScan Generic 云端复核。每种方法分别显示 AI/正常拍摄百分比、单项结论、AI 率较高与较低的采样帧和秒数。汇总报告显示通过、未通过与证据不足的数量。传统频谱和连续性指标作为辅助取证，不参与概率投票。

视频生成前的场景选择使用本地 `Qwen3-1.7B Q8_0`，通过本机编译的 `llama.cpp` CUDA 后端运行；台词不会提交给外部 LLM。模型只在固定的九类环境中选择一个。SDXL 只生成不含人物的新背景，U2Net 分割原图人物并以原像素合成，因此不会重新生成或改变脸部。SadTalker、EchoMimic V1、JoyVASA 和 EchoMimic V3 使用 768×768 方形肖像；TokenHub HumanActor 使用 768×1024 竖版肖像。实测单次场景分类约 1.5 秒，四类中文回归样例均得到预期环境。

网页默认选择当前本地样片中身份保持更稳定的 SadTalker。其输出使用扩展方形人脸区域，不回贴到原图；大幅张嘴时仍可能拉扯嘴型。JoyVASA 输入关闭裁剪旋转，直接保留模型原生方形结果。

账号防范分析也复用本地 `Qwen3-1.7B Q8_0`，由 Ubuntu `/account-analysis` 生成双语正文，Windows `account_llm.py` 保留证据规则与账号类型、验证模型输出及来源。模型仅接收已整理文字，不接收原始媒体，也不接入外部服务。来源标识区分本地 LLM 与失败时的规则草稿；手动更新失败不覆盖上次报告。GPU 推理与视频/检测任务互斥。该模型是文本 LLM，不是 VLM。

自动背景替换已在每个视频任务生成前调用 `prepare_video_portrait`：Qwen 按台词选择环境，SDXL 生成空背景，U2Net 保留原图人物像素。只有工作台生成语音携带 `source_text` 时，前端才会把台词传给场景分类器；直接上传的音频目前不自动转写，因此选择默认 `neutral_studio`（中性背景），并非跳过背景生成。SadTalker 的方形脸部裁剪可能让背景露出较少。

检测模型独立分析同一组对齐人脸帧。视频边界使用 `D:\project\data\real` 的 17 个真实视频和 `D:\project\data\fake` 的 22 个去重生成视频离线拟合。透明规则为 GenD、UCF、RECCE、F3-Net 的真实分布包络与整幅画面时序变化的并集；NPR 在当前视频域只展示、不投票。当前 39 个校准样本回放为 39/39，其中真实 17/17、AI 22/22。这是当前小样本拟合结果，不是未知互联网视频的准确率。资源 ID、文件夹、文件名、文件哈希、生成任务记录和媒体元数据不参与线上检测结论。

生成子进程改编自原 `talking_head_webui_app.py` 的 FFmpeg/SadTalker 流程。Chatterbox 使用多语言接口。各模型使用独立环境并复用已验证的 CUDA 运行时；运行任务不通过 Git 更新仓库，也不自动下载模型权重。首次安装新模型使用 `install-sota-generators.sh`，脚本只在源码目录不存在时克隆，并固定兼容依赖版本。

输入上限500MB；音色克隆参考素材支持音频以及 MP4、MOV、WebM、MKV、AVI、M4V 视频，视频会在本地提取第一条音轨并取前20秒；视频驱动音频最长60秒；单个任务最多运行1小时。文件留在本机 `data/` 中，没有自动清理；关闭服务后可按任务目录手动删除。
