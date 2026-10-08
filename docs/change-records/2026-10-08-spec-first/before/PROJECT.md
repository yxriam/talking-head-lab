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

## 当前进度

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
