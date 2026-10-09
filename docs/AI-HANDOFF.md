# 当前交接（Codex / Claude 共用）

只写**现在的状态和下一步**，保持一页以内。过程与证据在 `docs/change-records/`，不要把流水账写在这里。

更新：2026-10-10 02:05（Pacific/Auckland），Claude。

## 现在的状态

| 项目 | 状态 |
|---|---|
| 源码 | 唯一源码 `D:\project\facebook\talking-head-lab`，分支 `refactor/module-layout`，未推送；`main` 与远端仍在 `5026841` |
| 运行服务 | 已切换到本仓库：3100 界面、8003 采集、WSL 8002 推理均来自这里（Codex 完成 T0–T3，AC01–AC05 通过，88 项程序测试与前端构建通过） |
| 功能实测 | Claude 在运行中的网站完成 T4：爬取、导出、账号分类、私人账号分析、音色克隆、四个本地视频模型、检测与界面交接均通过；详情见 [切换记录](change-records/2026-10-09-module-layout/记录.md) |
| 修复 | `3097796`（超长语音报错显示真实原因、去掉 JoyVASA 残留的背景进度文字）已部署，报错已复验；`8293d12`（TruthScan 云端复核默认不勾选）已在界面确认 |
| 回退 | WSL 备份 `/opt/media-app/backup-before-module-layout.tgz`；旧目录 `D:\project\NZ\cv` 保持只读 |

## 下一步

1. 推送 `refactor/module-layout`（用户的 PowerShell 里 `git` 不在 PATH，需要用 git 的完整路径或由 Codex 推送）。
2. 开 PR，CI 两个 job 变绿后合并到 `main`；核对 GitHub 上 README 的图片与结构图。
3. 推送后把本文件和 `docs/STATUS.md` 更新为已发布状态。

## 等用户决定

- LICENSE 采用 MIT 仍是草案。
- 付费云端接口（腾讯 YT HumanActor、TruthScan）未实测，只确认了就绪状态。

## 并行任务（Codex，未完成）

Prompt Lab（本地 Qwen3.5-2B 提示词评测，网页 + 命令行）：规格 `docs/specs/local-prompt-lab.md`，记录 `docs/change-records/2026-10-09-prompt-lab/记录.md`。代码与测试在工作区**尚未提交**（`collector/eval/prompt_lab.*`、`tests/test_prompt_lab.py`、`inference/install/install-prompt-lab.sh`），程序测试有待修复重验，尚无模型或网页验收。它使用独立端口和模型目录，不影响 8002。这些未提交文件不属于目录重组任务，推送时不要夹带；`scripts\test.ps1` 会发现 `test_prompt_lab.py`，在它修好之前整套测试可能因此失败。

## 仍未解决

- 账号分析正文质量：10 个合成用例 7 个通过人工语义检查。
- `account-warning-conflicts.md` 的 T1–T4 未实现。
- 模型安装与评测脚本改路径后只做过语法检查。
- 图片检测对合成人像的判别偏弱（本次实测 5 个模型中 4 个判为真实）。
