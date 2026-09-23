---
name: flowguard-init
description: "只创建 docs/project/ 中的项目级十阶段文档"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

先运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" discover --json` 做只读检查。若用户已要求初始化 FlowGuard 文档且目标仓库明确，运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" init --json`。只创建 docs/project/ 下的 02/07/10；功能文档由 context bind 创建。不得自动执行 specify init 或 openspec init。
