---
name: flowguard-governance
description: "检查十阶段文档、证据与依赖对写码、提交和发布的门禁"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" governance --session <session> --action <read|spec_write|test_write|code_write|git_commit|release> [--path <path>] --json`。exit 2 时展示 code/message/missing/allowed_actions/fix，并用 `stage status` 定位 docs/ 阶段缺口。code_write 需要 01—07；git_commit 需要 01—09 与有效 tests/static_analysis/semantic_review；release 需要全部十阶段、发布证据、用户验收和依赖收敛。allowed=true 只表示当前可核验条件满足，不是用户验收。
