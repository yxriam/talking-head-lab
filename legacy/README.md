# legacy/ — 历史脚本（不是当前入口）

这里保留项目早期的一次性脚本和工具，用于追溯实验来源。它们不参与当前产品的运行，路径多为当时机器的绝对路径，不要直接运行。

| 目录 | 内容 | 现在由谁取代 |
|---|---|---|
| `cloud-scripts/` | 云端 GPU 实例上的 Chatterbox、SadTalker、MuseTalk 跑批脚本 | `inference/generate.py`、`video_profiles.py` |
| `gradio-webui/` | 最早的 Gradio 单页界面及启动脚本 | `web/app/studio/` |
| `facebook-scam-viewer/` | 早期的静态账号查看器与网页生成提示 | 工作台的“爬取信息”页 |
| `offline-curation/` | 历史采集数据的离线整理脚本 | 采集服务的 ZIP 导出 |
| `facebook_capture/`、`facebook_intel_pipeline/` | 更早的两套采集试验说明 | `collector/facebook.py` |
| `report-tools/` | 一次性的实验报告与交接包生成脚本 | — |

当前入口见根目录 [README.md](../README.md)。
