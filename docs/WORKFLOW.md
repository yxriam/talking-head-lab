# 维护流程

规范在 [AGENTS.md](../AGENTS.md)；这里是一次改动从开始到交付的步骤。

## 1. 开始

```powershell
git status --short
git log -1 --format="%H %s"
```

新功能或行为变化：从 [任务规格模板](templates/task-spec.md) 建 `docs/specs/<任务>.md`，写清目标、范围、非目标、验收用例和停止条件。小修和纯文档可以跳过。

## 2. 实现与验证

只改规格范围内的文件。完成后先看 `git diff`，再对照验收用例。

| 改了什么 | 至少验证 | 可以说 |
|---|---|---|
| 文档 | 链接、实际 diff | 文档已更新 |
| `collector/` 账号链 | `tests/test_account_*.py` | 程序测试通过 |
| `collector/` 采集 | `tests/test_crawl.py` | 程序测试通过；真实采集另测 |
| `inference/` | `tests/test_server.py` 及相关测试 | 程序测试通过；模型效果另测 |
| `web/` | `npm run build` | 构建通过；行为另测 |
| 提示词或模型 | 冻结用例的真实模型实跑，保留原始输出 | 仅已跑的用例通过 |
| 部署 | `scripts\deploy-inference.ps1` 的输出与健康检查 | 已部署并验证健康 |

`scripts\test.ps1` 一次跑完全部程序测试和前端构建。

## 3. 提交与推送

```powershell
git add -- <本任务的文件>
git diff --cached --stat
git commit -m "type: summary"
git push origin <分支>
git ls-remote origin refs/heads/<分支>
```

一次提交一个任务；推送后核对远端提交号。需要 PR 时使用 [PR 模板](../.github/pull_request_template.md)。

## 4. 部署

源码提交不等于网站生效。

- `inference/` 变更：`scripts\deploy-inference.ps1`。
- `collector/` 变更：`scripts\stop.ps1` 再 `scripts\start.ps1`。
- `web/` 变更：开发模式自动生效。

## 5. 回退

已推送的提交用 `git revert <提交号>` 再推送，不强推。已经部署的推理服务需要在回退源码后重新运行 `deploy-inference.ps1`。

## 6. 记录

更新 [AI-HANDOFF.md](AI-HANDOFF.md)（只留当前状态与下一步）。有模型实测、部署或失败需要留证据时，用 [变更记录模板](templates/change-record.md) 在 `docs/change-records/<日期-任务>/` 记录。
