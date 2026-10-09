# 开发指南

[中文](DEVELOPMENT.md) · [English](DEVELOPMENT.en.md) · [返回首页](../../README.md)

按功能模块组织。改哪个功能，只读对应一节；每节的顺序都是：**做什么 → 数据怎么流 → 代码在哪 → 怎么扩展 → 怎么验证**。

- [总览](#总览)
- [① 爬取](#-爬取)
- [② 社工分析](#-社工分析)
- [③ 生成](#-生成)
- [④ 检测](#-检测)
- [工作台前端](#工作台前端)
- [测试、部署与提交](#测试部署与提交)

## 总览

三个进程，两条代理：

| 进程 | 目录 | 端口 | 运行位置 | 负责 |
|---|---|---|---|---|
| 工作台 | `web/` | 3100 | Windows（Node） | 界面；把 `/crawl/*` 转到 8003，`/api/*` 转到 8002 |
| 采集服务 | `collector/` | 8003 | Windows（Python） | 浏览器采集、任务历史、ZIP 导出、账号分析的规则与桥接 |
| 推理服务 | `inference/` | 8002 | WSL Ubuntu（GPU） | 语音、视频、检测任务队列，本地 Qwen |

两个服务目录内部都是**平铺的 Python 模块**（`import account_risk` 这种写法），不是包；这样推理服务可以原样同步到 GPU 主机的 `/opt/media-app/local-media/`。跨目录引用只出现在 `tests/` 和 `collector/eval/`，由各自的 `_paths.py` 处理。

## ① 爬取

**做什么**：用一个已登录的真实浏览器打开 Facebook 链接，滚动若干次，收集当前可见的文字和媒体。不调用私有接口，不绕过访问控制。

**数据流**：`CrawlPanel.tsx` → `POST /crawl/jobs` → `crawl_server.py` 建任务、单线程执行 → `facebook.collect()` → 结果写入 `collector/crawl-data/<任务 ID>/result.json` 与媒体文件 → 前端轮询 `GET /crawl/jobs/{id}`。

| 文件 | 职责 |
|---|---|
| `collector/facebook.py` | `login()` 打开登录窗口；`collect()` 滚动、提取可见文字、去重；`download()` 保存媒体并限制总大小 |
| `collector/crawl_server.py` | 任务队列、取消、历史、媒体读取、ZIP 导出、触发账号分析 |
| `web/app/studio/CrawlPanel.tsx`、`crawl-api.ts` | 采集设置、结果预览、素材带入其他模块 |

**结果结构**（`crawl-api.ts` 的 `CrawlResult` 是唯一定义）：`text[]` 每条带 `source_url`、可选 `date` 和 `context`；`media[]` 每条的 `status` 是 `downloaded`、`link_only`、`failed`、`duplicate` 之一。拿不到的字段留空，不补造。

**怎么扩展**

- 多采一个字段：在 `collect()` 的提取处加字段 → 同步 `CrawlResult` 类型 → 如需展示再改 `CrawlPanel.tsx`。来源链接和时间必须一路保留。
- 支持新平台：新建 `collector/<平台>.py`，实现同样签名的 `login` / `collect` / `download`，在 `crawl_server.py` 按链接域名选择采集器。输出结构保持一致，后面的分析和素材交接就不用改。

**验证**：`tests/test_crawl.py`（用真实浏览器访问本地模拟页面，不访问 Facebook）。真实采集需要手动登录后在工作台实测。

## ② 社工分析

**做什么**：从采集到的可见文字里找出可能被社会工程利用的信息，说明利用条件、后果和对应的防范动作。只分析私人账号。

**数据流**

```text
采集结果
  → account_risk.analyze()        先分类：私人 / 企业机构 / 无法确定
      └ 非私人：只返回分类依据和跳过说明，到此结束
  → account_risk 规则匹配          得到带证据编号的风险行
  → account_story                  整理人物关系、联系方式、原文引用，生成中英规则草稿
  → account_llm.prepare_material() 准备模型输入（长度上限、未被规则引用的原事实）
  → POST :8002/account-analysis    → local_account_model.generate()  本地 Qwen 改写
  → account_llm 校验               证据编号必须来自允许集合；失败则退回规则草稿并注明原因
```

| 文件 | 职责 |
|---|---|
| `collector/account_risk.py` | `RULES` 规则表、账号用途分类、`analysis_scope()` 门控 |
| `collector/account_story.py` | 关系、邮箱、原文描述的整理与纯文字输出 |
| `collector/account_llm.py` | 与推理服务的桥接、材料准备、输出校验、回退 |
| `inference/local_account_model.py` | 提示词、GBNF 语法约束、矛盾检查、调用 llama.cpp |
| `web/app/studio/AccountRiskReport.tsx` | 报告展示 |

**必须守住的约定**（规格在 `docs/specs/private-account-analysis-gate.md` 和 `account-warning-generalization.md`）

- 先分类后分析；企业和无法确定的账号不进入风险规则，也不调用模型。
- 生产提示词里不能出现某个具体人物、邮箱或个案答案；用例只放在 `collector/eval/data/`。
- 原文引用保持原语言原文；资料里的指令只当数据。
- 不输出概率、人物画像、诈骗话术。

**怎么扩展**

- 加一条规则：在 `RULES` 里加一个 `Rule(key, focus, pattern, weak_point, scenario, action, sentence, impact)`，并在 `tests/test_account_risk.py` 里补一条命中和一条不命中的用例。
- 改措辞或换模型：改 `local_account_model.py`。程序测试只能证明结构正确，**语义要靠真实模型评测**：

  ```bash
  # 在 GPU 主机上
  python collector/eval/eval_account_general.py --cases collector/eval/data/cases.json --output <新文件>.json
  ```

  一次只改一个变量，保存原始输出，逐句检查重复、伪造引用和遗漏的防范动作。

**验证**：`tests/test_account_risk.py`、`test_account_story.py`、`test_account_scope.py`、`test_account_llm.py`。

## ③ 生成

**做什么**：音色克隆（参考声音 + 台词 → 语音）和人像视频（照片 + 语音 → 视频）。照片原样进入模型，不换背景。

**数据流**：`Studio.tsx` → `POST /api/media` 上传得到资源 ID → `POST /api/jobs` → `server.py` 排队，GPU 任务一次只跑一个 → 子进程 `generate.py <voice|video>` 在对应模型自己的虚拟环境里运行 → 结果成为新的资源 ID，可直接交给下一步。

| 文件 | 职责 |
|---|---|
| `inference/server.py` | 上传、资源读取、任务队列、`/health` 能力报告 |
| `inference/generate.py` | 调用 Chatterbox、SadTalker、EchoMimic V1/V3、JoyVASA |
| `inference/video_profiles.py` | 每个视频模型的构图、输出策略、最长时长，唯一来源 |
| `inference/tokenhub.py` | 可选的云端腾讯 YT HumanActor（经用户自己的 COS 中转） |

**怎么扩展（新增一个视频模型）**

1. `video_profiles.py` 的 `VIDEO_PROFILES` 加一项。
2. `generate.py` 加调用函数，输入输出路径沿用现有约定。
3. `server.py` 的能力检查里报告该模型是否就绪。
4. `web/app/studio/api.ts` 的 `VideoModel` 类型和 `Studio.tsx` 的选项。
5. 安装脚本放 `inference/install/`，并把运行时需要的文件加进 `inference/deploy/sync-runtime.sh` 的清单。

**验证**：`tests/test_video_profiles.py`、`test_server.py`、`test_tokenhub.py`。模型效果需要在 GPU 主机上实跑，`inference/verify/` 里有逐模型的验证脚本。

## ④ 检测

**做什么**：对图片或视频运行多个检测方法，分别给出结论，再汇总。

**数据流**：`POST /api/jobs`（`kind=detect`）→ `server.py` → 子进程 `detect.py <媒体> <模型目录> <report.json>` → 前端按 `DetectionReport` 展示。

| 文件 | 职责 |
|---|---|
| `inference/detect.py` | 抽帧与人脸裁剪；GenD、NPR、UCF、RECCE、F3-Net；频谱与连续性取证指标；汇总 |
| `inference/truthscan.py` | 可选的 TruthScan 云端复核 |
| `inference/benchmark/calibrate_*.py`、`validate_calibration.py` | 阈值校准 |

**方法结果结构**（`api.ts` 的 `DetectionMethod`）：`status`、`verdict`、`score`、`thresholds`、`evidence.high/low` 时间段。证据不足时 `status` 为 `insufficient`，不给分数。

**怎么扩展**：在 `detect.py` 里实现打分函数，用和现有方法相同的结构返回，加入方法列表即可；前端不需要改。阈值要用标注数据校准后再写入，不能凭感觉设。

**验证**：`tests/test_detect_thresholds.py`、`test_truthscan.py`。

## 工作台前端

`web/app/studio/` 是唯一维护的界面：

| 文件 | 内容 |
|---|---|
| `Studio.tsx` | 外壳、导航、语音/视频/检测三个面板 |
| `CrawlPanel.tsx`、`AccountRiskReport.tsx` | 采集与分析面板 |
| `api.ts`、`crawl-api.ts` | 两个后端的请求函数和全部类型定义 |
| `studio.css`、`crawl.css` | 样式 |

界面文字用 `T('中文', 'English')` 就地写双语。任务用轮询，网络错误时只重查已受理的任务，不重新提交。

## 测试、部署与提交

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1            # 全部程序测试 + 前端构建
powershell -ExecutionPolicy Bypass -File scripts\deploy-inference.ps1 # 同步推理服务到 WSL 并重启、检查健康
```

- 改了 `collector/`：重启采集服务（`scripts\stop.ps1` 后 `scripts\start.ps1`）。
- 改了 `inference/`：运行 `deploy-inference.ps1`；它按 SHA256 只复制变化的文件。
- 改了 `web/`：开发模式自动热更新。

“代码改了、测试过了、模型实测过了、已部署、线上验证过了”是五个不同状态，提交说明里写实际达到的那个。流程和提交规范见 [CONTRIBUTING.md](../../CONTRIBUTING.md)。
