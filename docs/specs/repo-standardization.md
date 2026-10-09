# 仓库规范化：目录归类、标准项目文件与 CI

- 需求来源：用户 2026-10-09 "请尽量让这个项目更加规范"。决定者：用户；执行：Claude（工作区）。前置：docs/specs/public-repo-cleanup.md。
- 目标：公开仓库具备开源项目的常规结构——根目录只有入口与规范文件；历史脚本有明确归属；有 LICENSE、CONTRIBUTING、SECURITY、.editorconfig、lint 配置、CI 与 Issue 模板；README 结构图与实际目录一致。
- 非目标：不改运行代码（local-media、facebook-scam 业务逻辑、前端）；不重排 local-media 内部文件；不清理既有脚本的未使用导入；不改模型、部署与服务。
- 约束：遵循 AGENTS.md；LICENSE 选择属用户决定，本轮按 MIT 起草，发布前由用户确认。

## 输入 / 输出契约

| 项目 | 变化 | 发布处理 |
|---|---|---|
| 根目录 9 个云端一次性脚本（generate_chatterbox_*、run_visa_*、inspect_a2h10、link_a2h10_torch、check_remote_torch_envs） | → legacy/cloud-scripts/ | git mv |
| 根目录 Gradio WebUI 6 个文件（talking_head_webui_*、start/stop/open_* 、TALKING_HEAD_WEBUI_README.md） | → legacy/gradio-webui/ | git mv |
| setup_autodl_key_upload.py（含租用实例主机/端口/密钥名） | → archive/legacy-demos/（已忽略） | git rm --cached |
| 网站启动说明.md | → docs/setup-guide.zh-CN.md；README 两处链接同步 | git mv |
| 新增 | legacy/README.md、LICENSE（MIT 草案）、CONTRIBUTING.md、SECURITY.md、.editorconfig、pyproject.toml（仅 ruff 配置）、.github/workflows/ci.yml、.github/ISSUE_TEMPLATE/{bug_report,feature_request,security}.md | git add |
| README.md / README.en.md | "项目结构"树更新为新布局；尾段指向 legacy/、docs/proposal/、CONTRIBUTING、SECURITY | 正常提交 |
| tools/build_claude_handoff.py | 4 处路径改指 legacy/ | 正常提交 |

## 验收用例

- AC1：根目录仅剩 README.md、README.en.md、AGENTS.md、CLAUDE.md、PROJECT.md、CONTRIBUTING.md、SECURITY.md、LICENSE、.editorconfig、pyproject.toml、.gitignore 与目录。
- AC2：README.md / README.en.md 中无指向已移动文件的断链。
- AC3：`python -m unittest test_account_story test_account_risk`（local-media）通过。
- AC4：ruff（E9/F63/F7/F82）对 local-media、facebook-scam/crawler、facebook_capture、facebook_intel_pipeline、tools 无报错。
- AC5：tools/build_claude_handoff.py 语法检查通过。
- AC6：首次 CI 运行两个 job 均绿（待推送后核对）。

## 停止条件

发布 checkout 不可访问时，只在工作区完成并写入 AI-HANDOFF 待办；不在工作区 git init。
