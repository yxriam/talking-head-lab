# AI 媒体教学网站

默认流程：**爬取信息与账号反诈分析 → 音色克隆 → AI 人像视频 → 视频真伪检测**。各功能仍可独立使用。
Facebook 采集完成后，分析区只显示具体文字：账号类型判断、原文中的具体称呼、联系方式与描述，以及有依据的防范措施。页面语言选择同步切换分析正文，ZIP 内的 account-analysis.txt 使用当前语言；原文引用保留原语言，不伪造翻译。取消类型卡片、证据表、缺失字段清单和无依据的补充；不输出人物攻击路径或诈骗话术。

## 主要维护位置

| 目录 | 用途 |
|---|---|
| `facebook-scam/video-forensics-web/app/studio/` | 已确认的中文界面，`Studio.tsx` 页面、`studio.css` 样式、`api.ts` 本地接口 |
| `local-media/` | Python 本地服务、模型调用、运行数据及安装状态 |
| `facebook-scam/crawler/facebook.py` | 唯一在线 Facebook 采集实现；其余 crawler Python 文件只用于历史数据离线整理 |
| `local-media/account_risk.py` | 可见文字与页面标记的反诈证据规则；不计算受骗概率或人物画像 |
| `local-media/account_story.py` | 具体关系、邮箱、原文描述与明确媒体标注的整理，以及纯文字输出 |
| `local-media/account_llm.py`、`local_account_model.py` | Windows 的本地模型桥接与 Ubuntu 的 Qwen 正文生成；不调用外部服务，不分析图片或音频 |

其他 CV 根目录脚本和素材是历史工作，保留原位置。原信号初筛首页也保留，不计入三个学术模型检测。

## 工作规范与账号警示新规格（2026-10-08）

所有 AI 工具先读 [AGENTS.md](AGENTS.md)；[CLAUDE.md](CLAUDE.md) 是同一规范的入口。实现前冻结需求、约束和验收条件，按可独立审查任务推进；实际 diff、测试输出、模型实测与部署状态分别留证据。

Cursor 入口为 [.cursor/rules/project.mdc](.cursor/rules/project.mdc)，维护步骤见 [docs/WORKFLOW.md](docs/WORKFLOW.md)，新任务使用 [规格模板](docs/templates/task-spec.md) 与 [变更模板](docs/templates/change-record.md)。技术栈、目录和产品/安全规则以 AGENTS 为唯一规范源；Node 要求见前端 package.json（当前 >=22.13.0）。

账号警示遵循 [重大矛盾证据与时间规格](docs/specs/account-warning-conflicts.md)：默认接受用户事实；重大防范不一致必须列出两条原文、各自时间、来源、具体控制缺口及对应动作。不能用“不代表”替代证据；不能把技术熟悉程度推成容易被骗。不同时间的变化需区分，缺时间明确标注，不补造。

**当前缺口**：现有 Qwen 矛盾检查只有布尔结论；source_facts 目前只传 id/text，尚未保留时间，也未输出防范影响。旧 Ray 实测不能视为新规格通过。规格中的 T1至T4 待实施，本轮只更新记录与上下文文件，没有改动运行代码或重启服务。

本轮实际变化、审查和回退材料见 [工作记录](docs/change-records/2026-10-08-spec-first/记录.md)。当前目录缺少有效 Git 元数据，保存前后快照与统一 diff；未初始化仓库、未生成提交号。

## 工程治理与完整项目发布（2026-10-08）

本轮契约见 [工程治理规格](docs/specs/engineering-governance.md) 和 [完整发布规格](docs/specs/github-project-publication.md)，实际文件、检查、提交与回退见 [治理变更记录](docs/change-records/2026-10-08-engineering-governance/记录.md)。新增根忽略规则、工具入口、维护流程、模板和 PR 检查表；业务实现、模型、提示词和部署未改动。

| 阶段 | 本轮状态 |
|---|---|
| 需求与验收 | 已记录：本地治理与完整源码发布分别验收 |
| 文档/配置修改 | 已完成；检查输出见本轮记录 |
| 业务代码修改、模型实测 | 未进行；本轮不适用 |
| 程序测试 | 导入基线检查仅记录实际结果，不能当新功能验收 |
| 同步部署、运行服务验证 | 未进行 |
| 独立 Claude Code 审查 | 未进行；未发现已安装 CLI，不把自查冒充独立审查 |
| GitHub目标 | 用户指定 yxriam/talking-head-lab，现有public仓库，连接身份yxriam具有push权限 |
| 根工作区 Git | .git为空，不初始化；原facebook-scam嵌套仓库不改动 |
| 实际提交/推送 | 已推送到talking-head-lab/main，658ca46源码、970d64e治理、3c27666阶段记录；设备登录后远端HEAD核对一致，最终收尾记录见本轮变更记录 |

发布checkout为D:/project/facebook/talking-head-lab，从用户目标真实clone获得Git元数据。源码复制不带原嵌套.git、不迁移既有facebook-scam历史；根忽略规则不会改变原独立子仓库的行为。后续维护和回退在真实发布checkout执行，源目录仍保留全部历史材料。

## 既有功能状态（历史记录，本轮未复验）

以下为本轮之前的实现与验证记录；保留既有事实，本轮未重新验证服务可达、模型输出或部署版本，不能作为新规格验收结果。

网页已连接 Ubuntu 本地 API，支持真实上传、资源 ID 交接和任务轮询。Chatterbox、SadTalker、UCF、RECCE、F3-Net 已完成真实 GPU 推理验证。人像视频页也已接入 TokenHub `YT-Video-HumanActor`，待配置用户自己的 TokenHub API Key 和 COS 存储桶后执行首次真实调用。完整本地流程和独立上传视频检测均已通过 API 验证；检测证据不足时返回“不确定”，不生成假分数。

Windows 本地开发：运行 `local-media/start-local.ps1`，打开 http://localhost:3100/studio 。WSL推理服务后续使用相同API，不改变页面。
采集服务在 Windows 运行于 `127.0.0.1:8003`，网页通过 `/crawl` 代理访问。首次安装 `local-media/requirements-crawl.txt`；登录由网页按钮打开独立浏览器窗口，用户手动完成。结果保存在 `local-media/crawl-data/`，会话在 `local-media/facebook-browser/`。

Ubuntu 运行文件位于 `/opt/media-app/local-media`，模型源码和 CUDA 环境位于 `/opt/media-models`。Windows 保留唯一 Git 工作区及现有网页环境；`local-media/sync-runtime.sh` 只同步发生变化的后端文件，并校验 SHA256，不执行 Git 下载。Ubuntu API 使用端口 8002，由 `media-app` 服务账户运行。

### 验证

后端：`local-media/.venv/Scripts/python.exe -m unittest discover -s local-media -p test_server.py -v`。

前端：在 `facebook-scam/video-forensics-web` 中执行 `npm run build`。

API测试只覆盖输入边界、资源复用/分段播放和未就绪错误，不代表模型推理验证。
采集验证：`local-media/.venv/Scripts/python.exe -m unittest discover -s local-media -p test_crawl.py -v`；含真实浏览器处理本地模拟页面，不冒充 Facebook 实采。已移除的旧源码可以从 `local-media/legacy-code-20261008.zip` 恢复，历史数据与素材未删除。
账号风险规则验证：`local-media/.venv/Scripts/python.exe -m unittest discover -s local-media -p test_account_risk.py -v`。历史成功采集记录可点击“分析账号信息”或“更新分析”，结论保存在该任务 `result.json` 与 ZIP 导出的 `account-analysis.txt`。
