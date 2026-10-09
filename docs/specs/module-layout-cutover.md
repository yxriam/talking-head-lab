# 目录重组后的切换、实测与发布规格（交给 Codex 执行）

- 日期/时区、版本：2026-10-09，Pacific/Auckland；1.0
- 需求来源：用户要求“项目更清晰、可维护、规范；整理后同步给 Codex 和 GitHub；确认网站每个功能都能正常使用”，并决定把项目独立出 cv 目录、按功能模块重组后重新部署。
- 初始状态与基线：仓库 `D:\project\facebook\talking-head-lab`，分支 `refactor/module-layout`，HEAD 见 `git log -1`，基于 `main` 的 `5026841`；远端 `origin` = `yxriam/talking-head-lab`，尚未推送。运行中的网站仍来自旧目录 `D:\project\NZ\cv`；WSL 运行目录 `/opt/media-app/local-media` 仍是旧部署。

## 目标与边界

目标：让本仓库成为实际运行网站的唯一源码——在本机完成环境准备、程序测试、推理服务部署和启动，对四个功能逐项实测，通过后推送到 GitHub 并确认 CI。

范围 / 允许改动：

- 为了让重组后的代码跑通而做的**最小修复**：`scripts/*.ps1`、`inference/deploy|install|verify/*` 中的路径或语法问题，`tests/` 与 `collector/eval/` 的导入路径，`.github/workflows/ci.yml`，文档里与实际不符的命令。
- `docs/AI-HANDOFF.md`、`docs/STATUS.md` 和本任务的变更记录。

非目标（不要做）：

- 不再调整目录结构，不重命名模块，不重构业务代码。
- 不修改提示词、模型、检测阈值、采集逻辑；账号分析正文质量问题不在本任务修。
- 不为了通过而删除、跳过或放宽测试。
- 不删除或修改旧目录 `D:\project\NZ\cv` 中的任何文件。
- 不调用付费云端接口（腾讯 YT HumanActor、TruthScan），除非用户另行同意。
- 不强推，不改写已有提交。

约束：遵守 `AGENTS.md`。真实 Facebook 采集只针对下面指定的公共主页；不采集其他个人账号，不把任何真实个人数据、登录态、采集原始数据或生成的音视频提交进仓库。

## 决策与责任

| 决策 / 动作 | 状态 | 执行责任 |
|---|---|---|
| 项目独立出 cv、按功能模块重组 | 用户已决定；Claude 已实现并本地提交 | Codex 不再改结构 |
| 切换运行服务到本仓库 | 用户已同意重新部署 | Codex 执行 T1–T3，先备份再部署 |
| 推送到 GitHub | 用户已要求同步；条件是 AC01–AC12 通过 | Codex 执行 T5 |
| 付费云端接口实测 | 用户未同意 | 只检查就绪状态 |
| LICENSE 采用 MIT | 草案，用户未明确确认 | 推送前在汇报里再提醒一次，不自行更换 |

## 任务拆分

按顺序执行；每个子任务完成后把实际输出写进变更记录再做下一个。

| 子任务 | 做什么 | 通过条件 |
|---|---|---|
| T0 备份 | 在 WSL 里把 `/opt/media-app/local-media` 中除 `data/`、`.venv/` 以外的文件打包到 `/opt/media-app/backup-before-module-layout.tgz`，记录其中 `server.py` 与 `local_account_model.py` 的 SHA256 | 备份文件存在且可列出内容 |
| T1 环境与程序测试 | `scripts\setup.ps1 -MigrateFrom D:\project\NZ\cv`，然后 `scripts\test.ps1` | AC01、AC02 |
| T2 部署推理服务 | `scripts\stop.ps1`，`scripts\deploy-inference.ps1` | AC03 |
| T3 启动 | `scripts\start.ps1` | AC04、AC05 |
| T4 功能实测 | 在 <http://localhost:3100/studio> 按下表逐项实测，至少完整走一遍界面流程，其余可用接口 | AC06–AC12 |
| T5 发布 | 推送分支，确认 CI，通过后快进合并到 `main` 并推送 | AC13、AC14 |
| T6 交接 | 更新 `docs/AI-HANDOFF.md`、`docs/STATUS.md`，写变更记录 | AC15 |

脚本是在无法执行 PowerShell 的环境里写的，首次运行可能有小问题：遇到就做最小修复，单独提交为 `fix: …`，并在变更记录里保留原始报错。

## 验收标准

每一条都要有可复查的证据（命令原始输出、任务 ID、文件 SHA256 或截图），写进 `docs/change-records/2026-10-09-module-layout/记录.md`。“脚本没报错”不算证据，要看下面写明的可观察结果。

### 环境、测试、部署

| 编号 | 场景 | 通过条件 |
|---|---|---|
| AC01 | 运行 `scripts\setup.ps1 -MigrateFrom D:\project\NZ\cv` | 退出码 0；`collector\.venv\Scripts\python.exe` 存在；`collector\facebook-browser\` 与 `collector\crawl-data\` 中有从旧目录复制来的内容；旧目录对应文件仍在 |
| AC02 | 运行 `scripts\test.ps1` | `tests/` 下 10 个测试文件全部被执行，0 failure、0 error，记录实际测试总数；前端构建成功。若有测试因重组而失败，修复的是路径或导入，不是断言 |
| AC03 | `scripts\deploy-inference.ps1` | 输出含 `RUNTIME_SYNC_VERIFIED` 与 `Inference API is healthy`；`/opt/media-app/local-media/sync-manifest.json` 中 `server.py`、`local_account_model.py`、`detect.py`、`generate.py` 的 SHA256 与仓库 `inference/` 下同名文件一致 |
| AC04 | `scripts\start.ps1` | 输出 `5/5 Startup complete.`；监听 8003 的 python 进程命令行指向本仓库的 `collector\.venv`；本仓库 `logs\web.log` 是本次启动新生成的；3100 上没有旧目录启动的残留进程 |
| AC05 | 健康检查 | `GET http://localhost:3100/api/health`：`status=ok`，`voice.ready`、`detect.ready` 为 true，`video.models` 中 `sadtalker`、`echomimic_v1`、`joyvasa`、`echomimic_v3_flash` 的 `ready` 均为 true。`GET http://127.0.0.1:8003/crawl/health`：`status=ok`、`session_saved=true`、`account_analysis.ready=true`。`tokenhub_humanactor` 与 `truthscan` 只记录 `ready` 值，不要求为 true |

### 功能实测（运行中的网站）

| 编号 | 功能 | 冻结输入 | 通过条件 |
|---|---|---|---|
| AC06 | 爬取 | `https://www.facebook.com/DonaldTrump/`，4 次滚动，勾选下载媒体 | 任务状态 `done`；文字条数 > 0；至少 1 张图片 `downloaded`；每条文字和媒体都有 `source_url`；拿不到的媒体标为 `link_only` 或 `failed` 而不是成功。遇到登录或验证页面则停止并报告，不反复重试 |
| AC07 | 导出 | AC06 的任务 | “导出 ZIP”返回 200，压缩包内含 `text.txt` 和已下载的媒体文件，中英文界面各导出一次 |
| AC08 | 账号分类（非私人） | AC06 的任务 | 分析结果为“企业 / 机构”或“无法确定”，只有分类依据和跳过说明；没有风险段落；`generation` 不是 `llm`，推理服务日志里本次没有 Qwen 调用 |
| AC09 | 社工分析（私人） | ① 在 GPU 主机运行 `collector/eval/eval_account_general.py --cases collector/eval/data/scope-cases.json --output <新文件>`；② 在界面上对一条已迁移的、被判为私人的历史采集记录点“更新分析” | ① `scope_personal` 进入模型并返回中英文段落，`scope_business`、`scope_unknown` 被跳过。② 返回 `generation.kind=llm`、无 `fallback_reason`；中英文各至少一段，每段带非空证据编号且编号都能在该记录的原文中找到；正文中没有概率、人物画像或话术。只验收链路与结构，正文措辞质量按已知缺口记录，不作为本任务的失败项。若迁移来的历史里没有私人账号记录，② 记为未执行并说明，不为此去采集任何个人账号 |
| AC10 | 音色克隆 | `docs/showcase/reference-voice.wav` + 一句 3 秒以内的台词，再加一句约 5 秒的台词 | 两个任务均 `done`；输出可播放，时长在 0.2–60 秒之间；记录任务 ID 与耗时 |
| AC11 | 人像视频 | `docs/showcase/synthetic-input.png` + AC10 的语音；四个本地模型各一次，`echomimic_v3_flash` 使用 4 秒以内的那段 | 四个任务均 `done`，输出 MP4 同时含视频流和音频流；任务输入图片的 SHA256 与上传的原图一致，任务目录里没有背景替换产物。另做一次反例：把超过 4 秒的语音交给 `echomimic_v3_flash`，应返回“驱动语音需在 4 秒以内”的明确错误而不是崩溃或静默截断 |
| AC12 | 真伪检测与交接 | 用界面上的“检测这个视频”按钮直接检测 AC11 的 SadTalker 输出（不下载再上传）；再上传 `docs/showcase/synthetic-input.png` 检测一次图片 | 任务 `done`；报告含汇总和 `gend`、`npr`、`ucf`、`recce`、`f3net` 五个方法，每个方法要么有结论和阈值，要么明确为证据不足，没有空分数冒充结果；“克隆 → 视频 → 检测”至少有一次完全通过界面按钮交接完成；界面切换到 English 后四个页面文字为英文、浏览器控制台无新增错误 |

### 发布与交接

| 编号 | 场景 | 通过条件 |
|---|---|---|
| AC13 | 推送前检查 | `git status` 除忽略文件外干净；`git ls-files` 中没有 `.env`、登录态、`crawl-data`、模型权重、日志、个人或生成的音视频；本任务产生的修复都是独立的 `fix:` 提交 |
| AC14 | 推送与 CI | `git push origin refactor/module-layout` 后远端提交号与本地一致；开 PR 或直接推送触发的 CI 中 `Python lint and program tests` 与 `Web build` 两个 job 均为绿色。CI 红了就修到绿，再 `git checkout main && git merge --ff-only refactor/module-layout && git push origin main`，核对 `origin/main` 提交号。GitHub 上 README 中英文的图片、GIF 和 mermaid 结构图都能正常显示 |
| AC15 | 交接 | `docs/AI-HANDOFF.md` 改为切换后的实际状态（仍保持一页）；`docs/STATUS.md` 与事实一致；变更记录按编号列出每条 AC 的结果、证据位置、失败与修复、未做的事 |

## 停止条件与未完成项

- 同一个失败尝试 3 次仍未解决，或解决它需要改业务逻辑、提示词、模型、目录结构：停下，保留现场和原始输出，向用户报告，不绕过。
- `scripts\deploy-inference.ps1` 报缺少模型目录：说明该模型没装，不在本任务里重新安装，记录后继续验收其余功能，对应 AC 标为未通过。
- AC01–AC12 有未通过项时不执行 T5，不合并到 `main`。
- 已知且不属于本任务失败的缺口：账号分析正文质量（10 个合成用例 7 个通过人工语义检查）；`account-warning-conflicts.md` 的 T1–T4 未实现；模型安装与评测脚本只做过语法检查。

验证分层：环境准备、程序测试、部署、运行服务验证、提交、推送分别记录实际达到的状态，没做的写没做。

## 回退

- **网站与采集**：`scripts\stop.ps1`，再到旧目录运行 `D:\project\NZ\cv\local-media\start-local.ps1`。
- **推理服务**：在 WSL 中把 T0 的备份解包回 `/opt/media-app/local-media`，`systemctl restart local-media.service`，用 `/api/health` 确认。
- **源码**：分支未合并时直接放弃分支；已合并到 `main` 后用 `git revert`，不强推。

## 汇报格式

完成或停止时，给用户一张表：AC 编号、通过 / 未通过 / 未执行、一句话证据、证据位置。然后单独列出：做了哪些 `fix:` 提交、哪些功能没验到及原因、需要用户决定的事（LICENSE、付费接口是否实测）。
