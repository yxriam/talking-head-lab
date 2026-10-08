# 项目维护与发布流程

遵循 [AGENTS.md](../AGENTS.md)。[PROJECT.md](../PROJECT.md) 是现状索引；任务规格是验收契约，变更记录是真实证据。Claude/Cursor 入口仅引导读取同一规范。本流程不替代用户对架构、安全和范围的决定。

## 开始一个可验收任务

1. 完整读取共享规范、项目索引和相关规格。从 [任务规格模板](templates/task-spec.md) 建立 `docs/specs/<任务>.md`，冻结需求来源、约束、输入/输出、失败用例和停止条件。一次会话完成一项可单独审 diff 的交付。
2. 核对真实仓库根、分支、远端、HEAD、暂存与未提交状态，保存任务开始基线。独立子仓库另查；目录链接路径与真实目录可能不同。不要打印 `.env` 或凭据来排查身份。
3. 按 [变更记录模板](templates/change-record.md) 记录用户决定和 AI 的实现责任。新增架构、安全边界、公开范围或范围取舍先交人决定；常规实现自行推进。

```powershell
Set-Location D:\project\cv
git rev-parse --show-toplevel
git status --short
git branch --show-current
git remote -v
git log -1 --format="%H %s"
git diff --cached --name-only
```

Git 任一关键状态不可用时走下面的快照流程，不执行 git init。当前根 `.git` 为空；`facebook-scam/` 的有效仓库只是该子目录，不是整个项目的提交位置。

## 实现、审查与验证

沿用现有代码风格，只改规格范围。修改前保留旧文件；模型实验先保存冻结输入、参数、提示词版本和最大尝试次数，单次只改一个有理由的变量。

实现后先看 `git diff -- <本任务文件>`（无 Git 时看统一 patch），再逐项对照验收用例和实际输出。记录未通过项、修复及剩余缺口。Codex 完成实现与自查；Claude Code 只有实际独立只读审查后才记录工具、调用范围、具体发现和复核结果。不可用写“未进行”及原因，不安装新工具或把自查冒充独立审查。

| 改动 | 必要验证 | 通过后的准确表述 |
|---|---|---|
| 文档、规则与忽略配置 | 本地引用、规则一致性、实际 diff、Git 原生忽略正反例 | 文档/配置验收通过 |
| 账号链 | AGENTS 指定 account_llm；按范围加 account_risk/account_story | 对应程序测试通过 |
| server.py 或 API | test_server.py；输入边界与兼容性 | API程序测试通过 |
| 前端行为 | 在 facebook-scam/video-forensics-web 执行 npm run build；Node >=22.13.0 以 package.json 为准 | 构建通过，行为验收另记 |
| 提示词/模型输出 | 冻结用例矩阵的真实模型实跑，留原输出、耗时与失败项 | 仅已跑矩阵模型实测通过 |
| 部署 | 同步清单与 SHA256、重启结果、运行服务版本及受影响功能验证 | 同步、重启、运行验证分别记录 |

文档任务不重跑 GPU 或整站测试。程序通过不等于模型通过；模型通过不等于已部署。PROJECT 中历史状态保留其适用范围，不作为新规格通过证据。

## 发布前检查与小步提交

根 `.gitignore` 防止环境、权重、凭据与生成素材进入未来根仓库，保留源码、规格、文本证据、公共网页资源及脱敏示例。独立子仓库使用自己的忽略文件；已跟踪的敏感文件即使新忽略也仍在历史中，须另开经用户确认的处理任务。忽略匹配不是凭据审计，首次发布还需检查实际待提交内容。

有效仓库且归属/可见性已确认后，使用具体文件列表（以下占位需替换）：

```powershell
git diff --check
git add -- <本任务文件1> <本任务文件2>
git diff --cached --name-status
git diff --cached --check
git diff --cached -- <本任务文件1> <本任务文件2>
git commit -m "docs: describe the accepted governance change"
git log -1 --format="%H %s"
git status --short
git push <已确认远端名> <当前任务分支>
git ls-remote <已确认远端名> refs/heads/<当前任务分支>
```

远端分支的提交号必须等于实际本地交付提交；推送失败保留本地提交与错误，不能写“已上传”。不要 `git add .` 夹带既有改动，不强推，不自动创建 PR。仓库要求 PR 时使用 [PR 检查表](../.github/pull_request_template.md)，实际创建后记录 URL。提交号可在记录中用任务后一次独立文档提交补齐，避免预填不存在的自引用提交号。

## 部署与回退

部署是另一阶段：只有任务要求更新服务时才使用现有 `local-media/sync-runtime.sh`，核对实际同步文件和服务重启、运行版本；不把修改工作区称为网页生效。前端部署按任务规格约定，不能用后端同步脚本冒充前端发布。

已共享的单个任务提交回退：先确认干净的任务范围和待保留用户改动，在对应仓库执行 `git revert <实际提交号>`，核对反向 diff，跑直接相关检查，再向原远端推送回退提交；多个任务按依赖逆序。不要对共享历史执行 reset --hard 或 force push。源码回退后，已部署服务需同步回退版本、重启并复验，否则只算工作区/仓库回退。

无有效 Git 时：

1. 在本轮变更目录保存 `before-manifest.json`（路径、原存在性、SHA256）及 `before/` 的旧文件快照；只保存本任务必要文件，避免复制素材与凭据。
2. 实现后保存 `after-manifest.json`、标准统一 diff 和验证结果，明确无提交号、未推送。记录新增文件和需要保留的证据目录。
3. 回退先比较当前文件 SHA256 与 after 清单。完全匹配才可恢复 before 文件、删除本轮新增文件；有后续修改则逐块人工逆向合并，不能整文件覆盖。实际回退应保留本轮证据目录。
4. 若 Git 可执行但根元数据无效，可在临时目录复制本轮文件，用 `git -c core.autocrlf=false apply --no-index --reverse --check <绝对patch路径>` 验证，然后在临时目录逆向应用并核对 before SHA256；不要借此初始化仓库。

根 Git 恢复来源、根项目目标远端及可见性、嵌套仓库如何维护由用户确认。恢复后再次核对基线和隐私；不要用子仓库 GitHub API 直接写根文件绕过归属决策。

## 交付与经验回写

变更记录逐项标出需求、代码、程序测试、模型实测、同步部署、运行验证、提交与推送的实际状态，附失败原因、文件清单、原输出位置、审查范围和回退步骤。最后核对实际 diff 与任务基线，回写一条可复用规则；未调用其他工具就明确未调用。

本轮治理规格见 [engineering-governance.md](specs/engineering-governance.md)，Git 缺口及实际验收见 [本轮记录](change-records/2026-10-08-engineering-governance/记录.md)。


## 完整项目发布 checkout

用户已指定 [yxriam/talking-head-lab](https://github.com/yxriam/talking-head-lab) 作为完整源码目标，现有public可见性不变。发布checkout为D:/project/facebook/talking-head-lab；源D:/project/cv根Git仍无效，不初始化、不移动原子仓库。参考 [发布规格](specs/github-project-publication.md)。后续在发布checkout开发或按本任务文件清单复制更新，审diff、相关验证后小步提交；不复制.git、媒体、数据或环境。历史脚本的个人音频示例路径仅在公开导出中脱敏，原文件保留本地，导出差异及SHA256在本轮清单记录；已发布源码为后续维护基线。
