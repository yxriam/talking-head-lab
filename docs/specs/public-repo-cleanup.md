# 公开仓库整理：去除根目录人名脚本与提案草稿

- 需求来源：用户 2026-10-09 决定（简历将链接本仓库，投递前整理公开面貌）。决定者：用户；执行：Claude（工作区）。
- 目标：公开仓库根目录不再出现以导师姓名命名的一次性演示脚本与媒体；提案/论文草稿移出根目录；共享文档中的人名改为中性称呼。
- 非目标：不改运行代码、接口、模型与提示词；不删除任何历史素材；不重写 docs/change-records 既有快照与 patch 中的历史记录。
- 约束：遵循 AGENTS.md（历史素材保留、不编造、不夹带）。本工作区根 Git 无效，提交在发布 checkout D:/project/facebook/talking-head-lab 进行。

## 输入 / 输出契约

| 项目 | 原位置 | 新位置 | 发布处理 |
|---|---|---|---|
| generate_ray_*.py（2）、run_ray_*.sh（3）、ray_*_preview.jpg（3）、ray_*.wav/.mp4（5） | 根目录 | archive/legacy-demos/ | `git rm --cached` 已跟踪的 .py/.sh；媒体原本已忽略 |
| tools/build_ray_methods_report.py | tools/ | archive/legacy-demos/ | `git rm --cached` |
| 提案与论文草稿 8 个（.tex/.md/build_*_pdf.py/figure_prompts） | 根目录 | docs/proposal/ | `git mv` |
| AGENTS.md L57、PROJECT.md 6 处 “Ray” | — | 改为“导师样本 / 导师授权样本” | 正常提交 |
| .gitignore | — | 追加 `/archive/` | 正常提交 |
| tools/build_claude_handoff.py | — | 两处路径改指 archive/legacy-demos/ | 正常提交 |

## 验收用例

- AC1：发布 checkout `git ls-files | grep -i ray` 仅剩 local-media/eval_ray_*.py（本轮不处理，见待办）。
- AC2：根目录无 .tex、无 build_*_pdf.py、无 figure_prompts_*.md。
- AC3：`grep -c "Ray" AGENTS.md PROJECT.md` 均为 0。
- AC4：`python -c "import ast;ast.parse(open('tools/build_claude_handoff.py').read())"` 通过。
- AC5：README.md / README.en.md 对本轮移动文件无断链（grep 无引用）。

## 停止条件

发布 checkout 不可访问时，只在工作区完成并写入 AI-HANDOFF 待办，由 Codex 镜像到发布 checkout 后提交推送；不在工作区 git init。

补充 AC6：提案迁移后两个 PDF/LaTeX 资源路径必须实际存在；允许仅修正移动导致的路径失效，正文与历史来源不改。
