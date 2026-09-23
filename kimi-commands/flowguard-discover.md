---
name: flowguard-discover
description: "只读发现目标 Git 项目、原生 SDD 体系、CLI 可用性与冲突，不初始化任何工具"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

执行 FlowGuard 的只读 SDD 发现：

1. 确认用户指定的真实仓库或模块路径，运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" discover --json`
2. 报告 Git/worktree、项目类型、`.specify/`、`openspec/`、Superpowers 产物与 CLI 可用性
3. 明确区分：CLI 已安装、Skill 已安装、项目已初始化
4. 若状态为 `choice_required`，停止创建规格并请求用户选择事实源
5. 若状态为 `assessment_required`，由智能体结合用户任务分类 read_only/simple_change/important_change/incident；不要静默初始化

本命令严格只读，不运行 specify init、openspec init 或安装。
