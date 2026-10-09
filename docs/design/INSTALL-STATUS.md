# 安装接续状态

2026-09-09 安装接续记录（已重启并成功安装）：

- WSL 2.7.13.0 / kernel 6.18.33.2-2 已安装。
- 默认 WSL 版本2；VirtualMachinePlatform Enabled。
- Windows 待重启状态已解除。
- Ubuntu-22.04 安装成功，安装日志 ExitCode: 0；Linux 已启动，系统为 Ubuntu 22.04.5 LTS。
- Linux 中 nvidia-smi 已识别 RTX 5070 Ti Laptop GPU，显存 12227 MiB，Windows 驱动 573.29 / CUDA 12.8。
- Python 3.10、venv、编译工具及 FFmpeg 已安装，linux-prepare.txt 记录 PREPARE_COMPLETE / ExitCode: 0。
- 尚未发现 UID 1000 普通用户。linux-status.txt 最后的 ExitCode: 2 来自 getent 查询无此用户，不能解释为显卡或 Ubuntu 启动失败。
- 普通 Codex 执行账户调用 WSL 服务返回 E_ACCESSDENIED，管理员账户 ALICE_YANG\10379 可读取状态。避免把发行版注册到隔离执行账户。
- 用户已取消 D 盘要求；Ubuntu 使用默认位置。
- 用户提供参考：https://zhuanlan.zhihu.com/p/2017602632177427017 ，已读取。无需执行其中的导出/注销/导入迁移步骤。

setup-models.sh 已成功完成，ExitCode: 0。PyTorch 2.7.1+cu128 已完成真实 CUDA 矩阵计算验证（GPU_VERIFIED）。三个官方模型仓库已下载到 /opt/media-models（SOURCES_READY），后续直接复用，不重复克隆或自动拉取。

后端 8 个运行文件已同步到 /opt/media-app/local-media；逐文件 SHA256 校验及 Python 语法检查通过，见 sync-runtime.log。当前 Windows data 目录没有需要迁移的已上传媒体。Windows .venv、node_modules、历史素材及安装日志不搬入 Linux。

后续同步运行代码使用 sync-runtime.sh：只复制内容发生变化的文件，不删除目标文件，不调用 Git。源码的唯一工作区现位于 D:\project\NZ\cv。

2026-09-11：Ubuntu 默认用户 alice 已完成初始化。应用不保存或使用用户密码；API 使用独立的无登录权限 media-app 服务账户。

Chatterbox 真实 GPU 推理通过，生成 3.68 秒 WAV；SadTalker 真实 GPU 推理通过，生成 3.71 秒 H.264/AAC MP4。当前生成流程不添加画面水印，两个 READY 标记均在输出完整性检查后创建。

2026-09-12 自然度对照后，SadTalker 默认参数设为 `--preprocess crop --still --pose_style 0 --expression_scale 1.0 --size 256`，不启用人脸增强。使用同一照片和 3.84 秒语音经完整 API 链路生成耗时 27.4 秒；输出为 256×256、25 fps、H.264/AAC。`expression_scale=0.8` 口型偏弱；不带 `still` 的版本眼镜、脸型和背景漂移更明显。

2026-09-12 已将官方 EchoMimic V1 accelerated audio pipeline 接入同一个 `/jobs` API 和 Studio 模型选择。SadTalker 仍为默认；EchoMimic V1 标为试验且限 20 秒。使用同一照片和 3.84 秒语音通过 API 实际生成耗时 62.9 秒，输出 384×384、24 fps、H.264/AAC；任务返回 `model=echomimic_v1`、实时扩散进度和 `elapsed_seconds`。同素材回归中 SadTalker 为 28.7 秒，Chatterbox 为 21.0 秒，均生成成功。

2026-09-12 质量边界复测：EchoMimic V1 accelerated 使用同一素材直接生成 512×512、3.959 秒视频，耗时 99.16 秒，峰值显存 5574 MiB，最大 RSS 7049856 KB。相较 384×384，清晰度提高但肩膀与躯干仍基本静止，确认主要限制来自模型架构而非 12 GB 显存。后续采用 `QUALITY-UPGRADE-PLAN.md` 中的视频扩散 Avatar 路线。

DeepfakeBench 的 UCF、RECCE、F3-Net 官方 v1.0.1 权重以及 NPR 官方权重已安装并记录 SHA256。当前模型作为同一个学习型视觉证据组运行；另有传统频谱和连续性分析。视频改为顺序解码与按时长自适应覆盖，图片可直接提交。汇总使用分类器原生边界计票并显示置信等级；NPR 已验证不能识别本机 SadTalker 输出，因此不参与“真实”投票。验证记录见 `DETECTION-DESIGN.md`。

Ubuntu API 已切换到 127.0.0.1:8002，三个后端边界测试通过，健康检查 platform=linux 且三项 capability 均 ready=true。完整 API 链路已验证：上传参考语音 → Chatterbox 输出 → 资源 ID 直接交接给 SadTalker → 输出视频 → 资源 ID 直接交接给三个检测模型；另行上传其他视频也已验证。

仍需注意：三个检测分数不是现实世界真实性概率，尚无本机代表性校准数据集，分歧或人脸不足时总体结论保持“不确定”。

2026-09-22：JoyVASA 官方模型已完成本机真实 GPU 推理，并通过统一 `/jobs` API 生成 4.28 秒带音频 MP4，API 用时 60.1 秒；该模型用于更明显的表情及头部姿态变化。EchoMimic V3 Flash 已固定兼容依赖、启用顺序 CPU offload，并修复官方 MoviePy 临时音轨相对路径问题；3.8 秒输入经统一 API 成功输出 3.72 秒、H.264/AAC 视频，用时 311.1 秒。V3 在本机约占 7 GB 内存及 16 GB swap，因此网页将它标为短片高质量慢速模式并限制输入到 4 秒。启动脚本会验证 WSL keeper 的进程类型并自动启用专用 swap，避免旧 PID 被复用或 WSL 自动退出导致任务中断。

2026-09-22：本地场景 LLM 固定为 Qwen3-1.7B Q8_0（1.8 GB），通过 CUDA 12.8 原生编译的 llama.cpp 在 RTX 5070 Ti 上运行。首次 GPU 单次推理耗时 1.69 秒、最大 RSS 约 2.1 GB；加入中文定义、少量示例、固定环境白名单和 GBNF 语法约束后，金融诈骗、菜谱、医疗建议和物理课程四类测试分别返回新闻演播室、家庭厨房、诊室和教室/图书馆。外部场景 LLM 文件已移除，台词只在本机处理。

2026-09-23：InstantID 本地身份保持肖像预处理完成真实 GPU 验证。源照片经“本地 Qwen 场景提示 → InstantID 换背景肖像”生成 768×768 办公室肖像；首轮冷启动总耗时 4 分 07 秒，其中 8 步扩散约 74 秒，最大 Python RSS 约 6.9 GB，GPU 峰值约 9.1 GB。AntelopeV2 对源图与生成图的人脸嵌入余弦相似度为 0.4907。网页中的所有视频模型均经过这一步；SadTalker、EchoMimic V1、JoyVASA 与 EchoMimic V3 Flash使用正方形输入，TokenHub HumanActor 使用 768×1024 竖版输入。

同日完成统一 API 端到端实测：上传原始人像与 3 秒驱动语音后，本地 Qwen 返回 `professional_office`，InstantID 完成肖像生成并自动交接给 SadTalker。最终输出为 2.432 秒、256×256、25 fps、H.264/AAC MP4，任务状态 `done`，网页和后端分别保持在 3100 与 8002 端口。

2026-09-25：按 Jev 定位结果修复 EchoMimic V3 Flash 启动失败。根因是顺序 CPU 卸载在 WSL 内造成超过 12 GB 的重复权重峰值；全 GPU 模式又会在 12 GB 显存边界加载 T5 时溢出。最终采用混合放置：Transformer 与 VAE 常驻 GPU，T5 与 CLIP 由 Accelerate 按需卸载，并在权重阶段执行 `malloc_trim` 归还 WSL 内存；`.wslconfig` 使用 14 GB 内存与 8 GB swap。两组不同照片/音频均成功生成 384×384、25 fps、2.299 秒、含音频的视频，耗时 521.1 秒与 548.9 秒，最大 RSS 约 13.28 GB，显存峰值 6.40 GB，8 步扩散约 18 秒。补丁已加入运行时同步与重装流程。

2026-09-23 质量修正：上述 InstantID 整人重绘结果被人工复核判定为脸部变形，0.4907 的嵌入分数不能证明视觉质量合格，因此该实现已撤下。替代流程使用 SDXL 仅生成空背景，U2Net 从原图分割人物并以原像素合成，脸部和身体不再经过扩散重绘。相同素材输出 768×768，耗时 45.97 秒，人脸嵌入相似度提升至 0.9942；网页提示和后台进度文字同步改为“保留原图人物像素”。

修正后统一 API 的 SadTalker 与 JoyVASA 任务均完成。SadTalker 张嘴帧仍存在旧模型固有的嘴型拉扯，因此网页默认模型改为 JoyVASA，SadTalker仅保留为快速选项。JoyVASA 禁用了人脸裁剪旋转，固定上下黑条在编码时直接裁除而不缩放脸部，最终输出为 512×448；8 帧人工复核中脸型、眼睛和鼻梁保持稳定。
