---
name: flowguard-evidence
description: "记录并查询与当前代码指纹绑定的测试、静态检查、语义审查和验收证据"
---

执行前确认已启用的 FlowGuard 插件根目录。若 Shell 环境未提供 `KIMI_PLUGIN_ROOT`，通过 `/plugins info flowguard` 定位安装目录并将下方路径改为绝对路径；不要在目标 Git 项目中猜测或执行同名脚本。

管理 FlowGuard 证据：

1. 先执行真实检查，不得仅凭模型声明 PASS
2. 记录：`python3 "${KIMI_PLUGIN_ROOT}/scripts/flowguard_state.py" evidence record --context-id <id> --kind <spec_verified|tests|static_analysis|semantic_review|user_acceptance|release_readiness> --producer <工具> --result <pass|fail|warning> --summary <摘要> --source-ref <报告或命令引用> --json`
3. 查询：`... flowguard_state.py evidence list --context-id <id> --json`
4. CodeGuard 结果只记 static_analysis/tests；CodeReview 结果只记 semantic_review；user_acceptance 只能来自用户明确确认
5. 代码或规格变化后，expires_on_change 证据会变成 stale，必须重跑

禁止把文件存在、HTTP 200、tasks 打勾或模型一句“通过”当成充分证据。
