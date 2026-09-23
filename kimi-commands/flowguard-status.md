---
name: flowguard-status
description: "读取 docs/ 十阶段项目与功能状态"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" stage status --task-id <task-id> --json`。展示 01—10 阶段状态、文档路径、失效原因和下一步；项目级 02/07/10 从 docs/project/ 读取，功能级七阶段从 docs/features/<task-id>/ 读取。不要用旧 status/current_feature 作为新任务的唯一事实源。
