# 历史记录

2026-10-09 目录重组之前的项目索引和 AI 交接全文，按原样保留用于追溯。其中的路径（`local-media/`、`facebook-scam/video-forensics-web/`、`D:\project\NZ\cv` 等）是当时的布局，对应关系：

| 旧路径 | 现在 |
|---|---|
| `facebook-scam/video-forensics-web/` | `web/` |
| `facebook-scam/crawler/facebook.py` | `collector/facebook.py` |
| `local-media/crawl_server.py`、`account_*.py` | `collector/` |
| `local-media/server.py`、`generate.py`、`detect.py` 等 | `inference/` |
| `local-media/test_*.py` | `tests/` |
| `local-media/start-local.ps1`、`start-crawl.ps1` | `scripts/start.ps1`、`scripts/start-collector.ps1` |

日常开发不需要阅读本目录；当前状态见 [../STATUS.md](../STATUS.md) 和 [../AI-HANDOFF.md](../AI-HANDOFF.md)。`docs/change-records/` 与 `docs/specs/` 中 2026-10-09 之前的文件同样使用旧路径。
