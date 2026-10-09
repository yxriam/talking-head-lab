# 参与开发

本项目用于反诈教学与安全研究。欢迎修复问题、补充检测方法、接入新模型或新平台的采集器。

## 开始之前

- 结构与各模块的扩展方式：[开发指南](docs/guides/DEVELOPMENT.md)
- 规范与产品约定：[AGENTS.md](AGENTS.md)（人和 AI 工具共用）
- 一次改动的完整步骤：[维护流程](docs/WORKFLOW.md)

## 提交改动

1. 新功能或行为变化先在 `docs/specs/` 写规格；小修和文档直接改。
2. 一次只做一件可以单独审查的事，沿用相邻代码的风格。
3. 运行检查：

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\test.ps1
   ```

   非 Windows 环境：`python -m unittest discover -s tests`，以及在 `web/` 里 `npm ci && npm run build`。
4. 提交信息使用 `type: summary`，类型为 `feat` `fix` `docs` `refactor` `test` `chore`。
5. PR 按 [模板](.github/pull_request_template.md) 说明改了什么、怎么验证的、实际达到了哪个状态（测试通过 / 模型实测 / 已部署）。

改提示词或模型时，程序测试不够：请附上冻结用例的真实模型输出。

## 不要提交

模型权重、虚拟环境、`.env` 和任何真实凭据、浏览器登录态、采集到的个人数据、个人或生成的音视频。详见 [SECURITY.md](SECURITY.md)。
