---
name: flowguard-context
description: "绑定会话、worktree、任务与原生规格，并创建 docs/ 阶段文档"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

先运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" discover --json`，再根据真实任务运行 `... flowguard_state.py context bind --session <session> --task-id <id> --task-type <read_only|simple_change|important_change|incident> --spec-system <none|spec-kit|openspec|superpowers|external> [--spec-ref <path-or-url>] [--parent-id <context-id>] --json`。可用 `context show` 或 `context list` 查看。绑定可写任务会在 docs/project/ 与 docs/features/<id>/ 创建缺失的十阶段文档。仅在用户明确确认后使用 `context approve --context-id <id> --approval scope_approved --actor user --json`；actor 文本不是可信用户回执，不得编造批准。
