# Talking Head Lab

本地 AI 媒体教学与反诈研究项目：Facebook 文字采集与账号防范分析、音色克隆、AI 人像视频及视频真伪检测。各功能可独立使用，默认在 Windows 采集/桥接、WSL Ubuntu 执行 GPU 推理。

## 项目入口

| 路径 | 内容 |
|---|---|
| [PROJECT.md](PROJECT.md) | 实际现状、模型与部署验证的适用范围、待完成项 |
| [AGENTS.md](AGENTS.md) | AI工具共享规范、技术栈、测试和安全边界 |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | 规格、实现、验收、发布、维护和回退 |
| [网站启动说明.md](网站启动说明.md) | 本机配置、启动、停止和排错 |
| [local-media/README.md](local-media/README.md) | FastAPI服务、GPU模型、接口和配置 |
| [facebook-scam/README.md](facebook-scam/README.md) | 采集服务与查看器 |
| `facebook-scam/video-forensics-web/` | React 19、TypeScript、vinext/Vite前端，主要工作台为 app/studio |
| `local-media/` | Python后端、规则、模型桥接、既有测试与部署脚本 |
| `docs/specs/`、`docs/change-records/` | 验收契约、真实变化和回退证据 |
| 根与 `tools/` 中的脚本/研究文档 | 历史辅助工作，保留来源；不是当前服务入口 |

## 环境与运行

前端 Node.js >=22.13.0，以 [package.json](facebook-scam/video-forensics-web/package.json) 为准；安装时使用锁文件。Python依赖分模型服务 [requirements.txt](local-media/requirements.txt) 与 Windows采集 [requirements-crawl.txt](local-media/requirements-crawl.txt)。GPU模型环境与路径详见上述安装文档，模型不随源码下载。

首次 clone 到不同路径时，先核对脚本内既有本机路径，不直接运行安装/部署脚本。现有 Windows 入口 D:/project/cv 指向 D:/project/NZ/cv；WSL运行代码 /opt/media-app/local-media，模型 /opt/media-models。日常启动使用 local-media/start-local.ps1，工作台地址 http://localhost:3100/studio。

仓库包含可维护的完整项目源码、前后端、配置示例、测试、脚本和文档。模型权重、虚拟环境、个人与生成媒体、采集数据、浏览器登录态、真实密钥、日志和本地工具安装包保留本机；克隆源码不代表本机运行环境或历史模型实测已重建。

真实凭据只写到本机配置位置，参考脱敏 env.example；不要提交到Git。Qwen仅接收整理后的文字，原资料指令按数据处理。TokenHub/TruthScan等可选外部接口按现有说明配置和授权，不改变默认本地分析边界。

## 更新和回退

每项变化先写规格、审实际diff、运行直接相关检查、保存真实状态，再做小步提交。详见 [维护流程](docs/WORKFLOW.md) 与 [首次完整发布规格](docs/specs/github-project-publication.md)。已共享提交使用 git revert，再验证与正常push；服务回退另需同步/重启/运行验证。

当前源码发布 checkout 为 D:/project/facebook/talking-head-lab，源工作区仍为 D:/project/cv。原工作区根Git无效且含独立 facebook-scam 仓库：不要在它运行git init或把子仓库当根仓库。后续更新应在真实发布checkout维护，或从原工作区按明确文件清单复制变化并重新审查；不能无差别同步数据与素材。

公开导入保留完整业务实现；历史脚本中个人音频路径/示例地址已在导出时替换为通用路径，原始脚本留本地。采集目标与带人物联系信息的历史实测原文不公开，历史摘要、验收规格与失败状态保留。详见首次发布清单与变更记录。
