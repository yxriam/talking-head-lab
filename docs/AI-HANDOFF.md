# 当前交接（Codex / Claude 共用）

## 2026-11-02 Cloudflare 展示站（当前）

| 项目 | 状态 |
|---|---|
| Git 基线 | 远端 main@1ca7a65；隔离 worktree D:\project\facebook\talking-head-lab-pages，分支 deploy/cloudflare-showcase。原工作区的领先提交和未提交改动保持不动 |
| 展示站 | showcase/ 已实现无依赖静态中文站，使用仓库既有公开合成素材；包含项目流程、三组视频、三类检测证据、可用性边界和 GitHub 链接 |
| 程序验证 | npm run test 通过：9 个素材复制，10 个必要输出存在，产物无本地 API 依赖 |
| 页面验证 | 桌面首屏、390×844 移动视口和移动导航通过 |
| 发布状态 | 尚未提交、推送或部署；Cloudflare 账号已登录，Pages 项目未创建 |

下一步：审查本任务 diff，提交并推送 deploy/cloudflare-showcase；在 Pages 使用根目录 showcase、构建命令 npm run build、输出目录 dist；发布后外网验证首页和媒体。

限制：展示站可全天在线；生成、采集和检测仍依赖本地 Windows/WSL/GPU。当前公开内容与 GitHub 公开仓库范围一致，不含个人媒体、日志或凭据。Claude Code 未调用。
