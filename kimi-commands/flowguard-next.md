---
name: flowguard-next
description: "由智能体判断十阶段的下一步，不由 Hook 自动推进"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" stage status --task-id <task-id> --json`，读取 docs/ 中 01—10 状态和原生规格引用。智能体结合用户目标、依赖与现有产物决定当前阶段；读取对应 flowguard-* 阶段技能，补充文档和验证证据。用 `... flowguard_state.py stage advance --task-id <task-id> --stage <01-requirements|...|10-release> --status in_progress --json` 标记开始。不要调用旧 next 命令推进新任务，不得代替用户验收。
