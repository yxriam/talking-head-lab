# 当前交接（Codex / Claude 共用）

只写**现在的状态和下一步**，保持一页以内。更早的记录在 `docs/change-records/` 与 `docs/history/`，不需要通读。

更新：2026-10-09（Pacific/Auckland），Claude。

## 现在的状态

| 项目 | 状态 |
|---|---|
| 目录结构 | 已按功能模块重组：`web/` `collector/` `inference/` `scripts/` `tests/` `legacy/`。分支 `refactor/module-layout`，基于 `main` 的 5026841 |
| 账号分析代码 | 已合入“先分类、只分析私人账号”与通用提示词（此前只在旧工作目录，未发布） |
| 文档 | README 中英文重写；AGENTS 精简；新增 `docs/STATUS.md`；开发与部署指南按模块重写 |
| 程序测试 | 不依赖 fastapi/httpx 的 45 项在本次会话通过；依赖它们的 5 个测试文件未能在会话环境运行，等 CI 或本机 `scripts\test.ps1` |
| 前端 | TypeScript 类型检查通过；完整构建未在会话环境运行 |
| 部署 | **未部署**。运行中的网站仍来自旧目录 `D:\project\NZ\cv` |
| 推送 | **未推送**。会话环境无法访问 GitHub 写入 |

## 下一步（按顺序）

1. 在本目录运行 `scripts\setup.ps1 -MigrateFrom D:\project\NZ\cv`，再运行 `scripts\test.ps1`。
2. `scripts\stop.ps1` 停掉旧目录启动的界面与采集，`scripts\deploy-inference.ps1` 同步推理服务，`scripts\start.ps1` 启动。
3. 在 <http://localhost:3100/studio> 逐项实测：采集、账号分析、音色克隆、各视频模型、检测。
4. 通过后推送分支并合并到 `main`，核对 CI 两个 job。
5. 旧目录 `D:\project\NZ\cv` 不再作为源码使用，只保留历史素材和数据。

## 仍未解决

- 账号分析正文质量：10 个合成用例中 7 个通过人工语义检查（订单、租房重复，求职英文引用失真）；导师样本回归遗漏防范段。见 `docs/change-records/2026-10-09-general-warning/模型验收记录.md`。
- 重大防范矛盾的时间与影响说明（`docs/specs/account-warning-conflicts.md` 的 T1–T4）未实现。
- 安装与评测脚本的路径已改为相对项目位置，只做了语法检查，未在 GPU 主机重新执行。
- LICENSE 采用 MIT 为草案，等用户确认。

## 回退

目录重组在独立分支上，`main` 未动：放弃分支即可回退源码。运行服务尚未切换，无需回退。
