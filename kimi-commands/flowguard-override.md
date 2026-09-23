---
name: flowguard-override
description: "旧十阶段兼容逃生通道；必须用户主动发起、填写理由并留痕"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

这是硬门禁的唯一逃生口，**只能由用户主动发起**；如果 agent 是自己想跳过阶段，立即停止。

1. 与用户确认三件事：要跳过的阶段（--stage，缺省=当前功能首个未收敛阶段）、理由（必填）、作用于哪个功能（--feature，缺省=当前功能）或项目级
2. 向用户复述后果：overridden 状态 + journal 留痕 + 后续审计可见
3. 用户确认后运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" override --reason <理由> [--stage <阶段>] [--feature <id>] --json`
4. 运行 `... status --json` 报告跳过后的流程状态

禁止：用 override 替代正常验收流程；为用户编造理由；连续跳过多个阶段而不逐个留痕。
