---
name: flowguard-stage
description: "查看和推进 docs/ 中的十阶段文档"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" stage status --task-id <task-id> --json` 查看阶段。写入 docs/project/ 或 docs/features/<task-id>/ 对应文档并自检后，可运行 `... flowguard_state.py stage advance --task-id <task-id> --stage <阶段文件名> --status in_progress --json`；只有真实用户批准或可审计依据才可将阶段标记 accepted/inherited/skipped。不能用模型自述伪造批准。
