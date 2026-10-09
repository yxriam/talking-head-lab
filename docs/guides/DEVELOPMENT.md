# 项目结构与二次开发

[中文](DEVELOPMENT.md) · [English](DEVELOPMENT.en.md) · [返回首页](../../README.md)

## 项目结构与代码分布

```text
talking-head-lab/
├─ README.md / README.en.md                 中文 / 英文入口
├─ facebook-scam/
│  ├─ crawler/facebook.py                   唯一在线采集实现
│  └─ video-forensics-web/
│     ├─ app/studio/                        四模块页面、样式、前端 API
│     ├─ build/sites-vite-plugin.ts         必需的 Vite 源码插件
│     └─ tests/                             前端既有检查
├─ local-media/
│  ├─ crawl_server.py / server.py            Windows采集 / WSL媒体 API
│  ├─ account_risk.py / account_story.py      文字证据规则与正文整理
│  ├─ account_llm.py / local_account_model.py 本地模型桥接与推理
│  ├─ generate.py / video_profiles.py        生成子进程、构图与时长策略
│  ├─ local_scene.py / prepare_scene.py      历史背景实验，未进入当前视频链
│  ├─ detect.py                             媒体检测和辅助取证
│  ├─ tokenhub.py / truthscan.py             可选外部接口
│  ├─ detector-runtime/                     检测安装注册源码
│  └─ test_*.py / *.sh / *.ps1               测试、安装、启动与同步
├─ docs/guides/                            部署 / 开发详解
├─ docs/proposal/                          研究提案
├─ docs/showcase/                           合成生成 / 实采样例与来源
├─ docs/specs/ / docs/change-records/        契约、变化、验证与回退
└─ AGENTS.md / CLAUDE.md / .cursor/rules/    共享协作规范与工具入口
```

研究提案位于 `docs/proposal/`，旧演示在本机忽略的 `archive/legacy-demos/` 保留来源；当前工作台从 `app/studio/` 维护。模型权重、虚拟环境、私人媒体、完整采集数据与真实凭据不在源码仓库；公开样例及来源在 `docs/showcase/`。

## 二次开发

### 修改什么，去哪里

| 要做的改动 | 入口与检查范围 |
|---|---|
| 改界面、布局或增加前端交互 | `Studio.tsx`、`CrawlPanel.tsx`、`studio.css`、`crawl.css`、`api.ts`；前端构建与行为检查 |
| 改采集字段 | `crawler/facebook.py`→`crawl_server.py`→账号规则/桥接/输出；保留来源与时间，运行采集测试 |
| 改账号提示或正文 | `account_risk.py`→`account_story.py`→`account_llm.py`→`server.py /account-analysis`→`local_account_model.py`；程序与真实模型分别验收 |
| 增加视频模型 | `video_profiles.py`、`generate.py`、`server.py` 能力/队列、前端模型选项；明确构图、时长、失败行为 |
| 改检测方法 | `detect.py` 与报告字段、前端显示；保留真实阈值、采样时段和证据不足状态 |

### 验证、同步与回退

先读 [AGENTS.md](../../AGENTS.md) 和 [PROJECT.md](../../PROJECT.md)，按[维护流程](../../docs/WORKFLOW.md)冻结任务规格、审实际 diff、运行直接相关检查，再做一个任务一个提交。

```powershell
local-media\.venv\Scripts\python.exe -m unittest discover -s local-media -p test_account_llm.py -v
local-media\.venv\Scripts\python.exe -m unittest discover -s local-media -p test_server.py -v
Set-Location facebook-scam/video-forensics-web
npm run build
```

按改动范围补充账号规则/正文、采集或模型相关检查。提示词修改需要冻结用例和真实模型输出，程序测试不能替代语义验收。

后端部署沿用 `sync-runtime.sh` 的 SHA256 同步，再重启并验证运行服务；脚本中的源路径需指向实际维护 checkout。源码提交、GitHub推送、运行部署是不同阶段。

```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/project/cv/local-media/sync-runtime.sh
wsl -d Ubuntu-22.04 -u root -- systemctl restart local-media.service
curl.exe http://localhost:3100/api/health
```

已共享任务用 `git revert <实际提交号>`，验证后正常 `git push origin main`。本轮的真实输入、耗时、失败修复、验证和回退见[展示变更记录](../../docs/change-records/2026-10-09-readme-showcase/记录.md)。
