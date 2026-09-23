---
name: flowguard-gate
description: "旧十阶段兼容门禁；新任务使用 flowguard-governance 检查写码/提交/发布"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

运行 flowguard 门禁自检：

1. 运行 `python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" gate --json` 查看四类动作整体放行状态
2. 对被阻塞的动作，逐条运行带 `--action <动作> --path <路径>` 的定向检查拿到诊断信封（severity/code/message/fix）
3. 把每个阻塞渲染成「动作 | code | 原因 | 解锁命令」表格
4. 运行 `... validate --json` 附带产物完整性问题（格式/追溯矩阵/测试文件存在性/Tier2 技能缺失）

只读操作：本命令绝不修改状态。被阻塞时给出最小解锁路径（通常 = 完成并验收某阶段），提醒用户 override 是留痕逃生口而非常规手段。
