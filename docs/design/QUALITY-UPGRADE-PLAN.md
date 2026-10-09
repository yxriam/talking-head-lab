# 人像视频质量升级方案

## 已确认的限制

- 当前设备为 RTX 5070 Ti Laptop 12 GB，Windows 物理内存约 16 GB；WSL 当前只分配 7.6 GiB 内存和 2 GiB swap。
- EchoMimic V1 accelerated 使用同一素材生成 384×384 视频耗时 47.53 秒、峰值显存 5.2 GB；512×512 耗时 99.16 秒、峰值显存 5.6 GB。提高分辨率不会用完显存，但只改善清晰度，没有让肩膀、躯干和姿态产生足够自然的运动。
- SadTalker 的 `--still` 会抑制眨眼与头部姿态；关闭它能增加头动，但本地对照出现眼镜、脸型和背景漂移。SadTalker 的生成范围仍以脸和头部为主。
- 因此主要瓶颈是模型能力。当前主机内存会限制依赖 CPU offload 的大型视频扩散模型。

## 目标模型

第一选择是 HunyuanVideo-Avatar。它直接使用人物图像和语音，目标就是生成带有面部情绪、头部、上半身或全身运动的视频。官方原生推理最低要求 24 GB 显存；官方 README 同时指向 WanGP 的 10 GB 低显存实现。

第二选择是 InfiniteTalk。它明确同时驱动嘴型、头部、身体姿态和表情，并支持图片加语音输入。低显存路径同样使用 WanGP/量化权重。

LongCat-Video-Avatar 1.5 作为高端方案保留。当前公开 vLLM-Omni 实测的 93 帧图片加语音流程峰值约 41 GiB 显存，不适合当前 12 GB 显卡。

## 设备方案

### 实用方案

- NVIDIA RTX 4090 24 GB 或 RTX 5090 32 GB
- 64 GB 系统内存，建议 128 GB
- 200 GB 以上可用 NVMe SSD
- Ubuntu 22.04/24.04 或 WSL2

这套设备优先部署 HunyuanVideo-Avatar，并保留 InfiniteTalk 做同素材盲选。现有 SadTalker 和 EchoMimic 继续作为快速回退。

### 高质量方案

- 48 GB 以上 NVIDIA GPU；LongCat-Video-Avatar 1.5 更适合 H100/A100 80 GB 或同级设备
- 128 GB 系统内存
- 300 GB 以上可用 NVMe SSD
- 原生 Linux

## 网站接入方式

网页仍只接收已有的人像照片与克隆语音。后端把语音克隆阶段已经存在的文字自动作为模型提示，不新增用户操作。生成任务保留同一个进度条，并返回模型加载、音频编码、扩散推理和视频封装的真实阶段进度。输出视频仍可直接送入检测页面。

## 验收

用同一张照片、同一段克隆语音和固定随机种子，对以下项目盲选：口型同步、身份与眼镜保持、眨眼、表情、头部运动、肩膀与躯干运动、背景稳定、跨帧闪烁。只有新模型在身体运动和总体自然度上明显超过 EchoMimic V1，才设为网站推荐模型。

## 官方来源

- SadTalker best practice: https://github.com/OpenTalker/SadTalker/blob/main/docs/best_practice.md
- HunyuanVideo-Avatar: https://github.com/Tencent-Hunyuan/HunyuanVideo-Avatar
- InfiniteTalk: https://github.com/MeiGen-AI/InfiniteTalk
- LongCat-Video: https://github.com/meituan-longcat/LongCat-Video
