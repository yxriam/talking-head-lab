# Claude Code 项目入口

先读取并遵循 [AGENTS.md](AGENTS.md)、[PROJECT.md](PROJECT.md) 和当前任务的 docs/specs/ 文件。共享的目录结构、编码标准、验收和回退规则只维护在 AGENTS.md，避免两套标准漂移；用户最新明确指令优先。

账号重大防范矛盾任务的契约是 [account-warning-conflicts.md](docs/specs/account-warning-conflicts.md)。审查时核对双方原文、各自时间、来源和具体控制缺口是否真的出现在输出中，不能只看 conflict=true 或 AI 的口头汇报。

进行独立审查时记录实际 diff、规格不符项、测试证据和剩余风险。没有运行 Claude Code 就不记录“Claude 已审查”。本轮仅建立入口文件，不表示已调用此工具。

日常交付按 [维护流程](docs/WORKFLOW.md)，需求与交付记录分别使用 [任务规格模板](docs/templates/task-spec.md) 和 [变更记录模板](docs/templates/change-record.md)。优先阅读实际 diff 与原始验证输出，再报告发现及复核；入口存在不等于本机安装或调用过 Claude Code。
