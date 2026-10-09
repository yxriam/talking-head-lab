# 项目状态

一页说明：现在什么能用、什么还没做完。细节在各规格和变更记录里。

## 功能

| 功能 | 状态 | 说明 |
|---|---|---|
| Facebook 采集 | 可用 | 登录后可见内容；文字、图片、视频链接、ZIP 导出、取消、历史 |
| 账号类型分类 | 可用 | 私人 / 企业机构 / 无法确定；只有私人进入分析 |
| 账号风险分析（规则） | 可用 | 证据编号可追溯，中英双语 |
| 账号风险分析（Qwen 改写） | 可用，质量待提升 | 10 个合成用例 7 个通过人工语义检查；失败时退回规则草稿 |
| 重大防范矛盾的时间与影响说明 | 未实现 | 规格 `specs/account-warning-conflicts.md` T1–T4 |
| 音色克隆（Chatterbox） | 可用 | 本地 GPU |
| 人像视频 | 可用 | SadTalker、EchoMimic V1、JoyVASA、EchoMimic V3 Flash；云端 YT HumanActor 需自备账号 |
| 真伪检测 | 可用 | GenD、NPR、UCF、RECCE、F3-Net + 取证指标；TruthScan 云端复核可选 |

## 工程

| 项目 | 状态 |
|---|---|
| 目录结构 | 2026-10-09 按功能模块重组（`web/` `collector/` `inference/`） |
| 路径 | 启动、部署、安装脚本均按自身位置推导，不再写死机器路径 |
| 程序测试 | `tests/`，不需要 GPU；CI 在每次推送时运行 |
| 模型安装脚本 | 在一台机器上验证过；重组后只做了语法检查 |
| 平台 | Windows + WSL2 Ubuntu 22.04；未在纯 Linux 或 macOS 上验证采集与启动脚本 |

## 文档地图

- 规格（验收契约）：[`docs/specs/`](specs/)
- 每次改动的证据与回退方式：[`docs/change-records/`](change-records/)
- 2026-10-09 之前的项目记录与交接全文：[`docs/history/`](history/)
- 检测方案设计、安装状态、质量改进计划：[`docs/design/`](design/)
