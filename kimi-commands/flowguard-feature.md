---
name: flowguard-feature
description: "旧十阶段兼容功能管理；新任务使用 flowguard-context 的父子任务与依赖"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

管理 flowguard 功能流水线。先确认用户想做哪个子命令：

**new <feature-id> --modules <模块...> [--title 标题]**
1. feature-id 必须是 kebab 格式（小写字母/数字/连字符）
2. --modules 必须是 project.json.modules 中已注册的模块（可多个，决定写码门禁的归属判定）
3. 运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" feature new <id> --modules <模块...> --json`
4. 报告生成的 7 份功能产物与下一步（/flowguard-next）

**list**：运行 `... feature list --json` 并渲染功能清单（状态/涉及模块）。

**done <id>**：先检查是否全部阶段收敛（未收敛会报未验收阶段清单）；如用户坚持放弃收口，引导用 drop 并写理由。

**drop <id> --reason <理由>**：理由必填，留痕 journal。

禁止跳过 CLI 直接手改 .flowguard/ 下的状态文件。
