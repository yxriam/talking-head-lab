# Facebook 采集与 AI 媒体工作台

日常入口：<http://localhost:3100/studio#crawl>。

## 维护这些位置

| 文件 | 职责 |
|---|---|
| `crawler/facebook.py` | Python + Playwright：登录、可见 DOM 提取、去重、原始媒体下载 |
| `../local-media/crawl_server.py` | 本机采集 API、后台任务、取消、历史、文件与 ZIP 导出 |
| `video-forensics-web/app/studio/CrawlPanel.tsx` | 第一步页面、采集设置、预览、素材交接与反诈报告 |
| `../local-media/account_risk.py` | 可见文字证据分析、账号用途/可见性、风险与防范对应、优先事项与结论 |

网页 `/crawl/*` 代理到 Windows 的 `127.0.0.1:8003`；模型 `/api/*` 继续代理到 Ubuntu 的 8002。采集使用独立浏览器配置与队列，不占用模型任务队列。

## 使用

首次依赖安装，在项目根目录运行：

```powershell
local-media\.venv\Scripts\python.exe -m pip install -r local-media\requirements-crawl.txt
```

`local-media/start-local.ps1` 会启动采集、模型服务和网页。只启动采集可以运行 `local-media/start-crawl.ps1`。

在“爬取信息”页打开 Facebook 登录窗口，手动完成登录；粘贴目标链接并采集。文字、媒体和失败记录保存在 `local-media/crawl-data/<任务ID>/`。浏览器会话仅保存在 `local-media/facebook-browser/`，不包含在结果导出中。
“爬取信息”是工作台第一项，`/studio` 默认打开此页。成功采集自动生成文字分析；旧成功记录可用“更新分析”刷新。分析区只保留文字和更新按钮，账号类型在文字开头判断；具体关系和完整邮箱按原文写出，建议落实到相应帖子和联系人。原始证据仍保存在任务 JSON 中，页面不再展示大表格或类型卡片。

`../local-media/account_story.py` 负责具体文字整理。父亲、母亲、侄子等称呼分别记录；英文 nephew 未说明亲属哪一侧时不会硬译为侄子。人脸/声音素材只按明确的配文或标注关联，未做身份识别；爱好、声音和性格描述只转述原文，不从照片、声调或兴趣猜性格。按用户要求，本地文字和导出呈现完整邮箱；验证码和长敏感标识仍遮盖。

账号类型和证据提取保留可核验的本地规则，正文使用本机已有的 `Qwen3-1.7B Q8_0`（llama.cpp CUDA）生成。Windows 采集服务通过本机回环地址调用 Ubuntu 的 `/account-analysis`；只发送有来源的文字草稿，不调用云端服务，不向模型发送原始图片、音频或浏览器会话。规则只覆盖明确文字线索，LLM 改写仍需要人工核对，未识别到风险不能视为安全结论。正常业务电话、转发和他人评论不直接当作本人风险；没有防范记录不等于没有防范意识。不生成诈骗话术或人物攻击方案。

正文把有依据的警示写为“可见信息 → 条件性的损失或暴露 → 对应核验动作”。`account_llm.py` 负责本机桥接、输出检查和保留类型判断，`local_account_model.py` 负责约束提示、原生 GBNF 输出及实际推理。新增邮箱、证据编号、亲属、个人描述和部分数字标识会被拒绝；这些检查不能证明模型的每个表述都正确。`generation` 记录实际 `kind`、`model`、推理时间，页面显示来源。自动采集时若推理失败，采集结果仍保留并明确标为规则草稿；手动更新失败不覆盖旧报告。LLM 与视频/检测任务互斥，不并发占用 GPU。

当前是 LLM，不是 VLM，不识别人脸或转写声音。背景场景分类继续复用同一份 Qwen 权重，账号生成使用独立提示，不修改背景流程。

页面右上角选择中文/English 时，分析正文与 ZIP 中的 `account-analysis.txt` 同步切换；原文引用保留原语言。`result.json` 保存 `narrative`/`conclusion`（中文）和 `narrative_en`/`conclusion_en`（英文），切换语言不重新采集，不发送资料给外部翻译服务。旧报告点击“更新分析”补齐两种语言。导出接口 `/crawl/jobs/<任务ID>/export?language=zh|en` 分别缓存 ZIP，更新分析会同时清理两种语言的派生缓存，原始材料保留。

只有下载成功的图片、视频或音频提供“用于生成/分析”按钮。按钮先把选中的本地文件交给现有媒体 API，取得资源 ID，再切换页面；不会自动生成语音或视频。视频页面链接、blob 流与无法下载的文件会保留状态，不会伪装成原视频。

图片默认最多 24 个，音视频最多 6 个；单图片最多 20 MB，音视频最多 100 MB，总量最多 500 MB。采集范围可选 4、8 或 20 次滚动。登录或验证页面会停止采集并提示用户操作。

## 验证与来源

```powershell
local-media\.venv\Scripts\python.exe -m unittest discover -s local-media -p test_crawl.py -v
local-media\.venv\Scripts\python.exe -m unittest discover -s local-media -p test_account_risk.py -v
local-media\.venv\Scripts\python.exe -m unittest discover -s local-media -p test_account_story.py -v
```

测试用真实 Playwright 浏览器读取本地模拟页面，验证去重、下载、历史、导出、取消、登录错误及地址边界；模拟内容不是实际 Facebook 采集结果。真实目标内容取决于登录账号可见范围与当前页面布局。

采集流程参考 <https://github.com/yxriam/facebook-scam> 的 `pipeline/pipeline.py` 与 `pipeline/extractors.py`。本版只保留页面采集与媒体整理，不加载关系推断、LLM、人脸识别或桌面录音。

## 历史代码与数据

2026-10-08：33 个重复采集/图谱/录音源码与未使用数据库模板文件已从当前维护路径移除；源码恢复包为 `../local-media/legacy-code-20261008.zip`。包内保留项目相对路径。

旧 `data/accounts/`、`data/final_accounts/`、分析报告与查看器保留。`crawler/curate_media.py`、`make_curation_sheets.py`、`build_simple_export.py` 是旧数据的离线整理工具，不在新网页的运行链路中。
