---
name: flowguard
license: Apache-2.0
description: Git 项目的智能体 SDD 治理入口。在会话开始、目标仓库或任务范围变化、开始写码、提交或发布前使用；发现 Spec Kit/OpenSpec/Superpowers 原生产物，分类任务并绑定会话+worktree+变更上下文，检查批准、依赖和证据。不复制规格正文，不自动初始化工具，也不以固定十阶段代替智能体判断。
compatibility: Python 3 标准库；Git 项目无需预先初始化 FlowGuard。原生 SDD 工具是否可用以 discover 结果为准。
---

# flowguard —— 智能体驱动的 SDD 治理

智能体负责语义判断和流程推进；Spec Kit、OpenSpec、Superpowers 提供原生规格与工程方法；FlowGuard 只保存治理元数据、校验证据并阻止绕过。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" discover --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" context show --session "$SESSION_ID" --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" governance --session "$SESSION_ID" --action code_write --json
```

## 智能体执行循环

1. **发现**：确认真实仓库/worktree、项目类型、项目指令、原生 SDD 标识、可用 CLI 和已有变更。
2. **定位**：判断 `read_only`、`simple_change`、`important_change` 或 `incident`，确认是已有变更、父功能、子功能还是实现任务。
3. **选择**：按“用户指定 → 项目指令 → 已有产物 → 已采用体系 → 默认规则”确定唯一规格事实源。
4. **绑定**：用 `context bind` 将会话 + worktree + task 绑定到原生规格引用；只保存引用，不复制正文。
5. **推进**：调用所选体系的真实命令或技能。Spec Kit/OpenSpec 管规格，Superpowers 管工程执行。
6. **验证**：运行真实测试、CodeGuard 静态检查和 CodeReview 语义审查，用 `evidence record` 绑定当前代码指纹。
7. **复核**：写码、`git commit`、发布前运行 `governance`；缺失时执行 `allowed_actions` 中的补救路径。
8. **恢复**：下一轮从 active 上下文、原生产物和有效证据继续，不重复生成已完成材料。

## 规格事实源选择

| 发现结果 | 行为 |
|:---|:---|
| 只有 `.specify/` | Spec Kit 是规格事实源 |
| 只有 `openspec/` | OpenSpec 是规格事实源 |
| 只有 Superpowers specs/plans | 延续 Superpowers 文档 |
| Spec Kit/OpenSpec + Superpowers | 前者管规格，后者管工程执行 |
| `.specify/` 与 `openspec/` 冲突 | 停止创建规格，请用户为本次变更选择 |
| 无体系 + simple/read-only | 不初始化完整 SDD |
| 无体系 + important Brownfield | 推荐 OpenSpec，说明文件影响后等待初始化批准 |
| 无体系 + important Greenfield | 推荐 Spec Kit，说明文件影响后等待初始化批准 |

## 必须由用户决定

- 首次 `specify init` / `openspec init`、工具安装升级或体系迁移。
- Spec Kit 与 OpenSpec 无法自动判定的冲突。
- 核心目标、非目标、验收标准和公共兼容范围变化。
- `scope_approved`、`user_acceptance` 和任何 override。

## 证据与插件分工

- FlowGuard：流程归属、前置条件、父子依赖、证据有效性和最终动作门禁。
- CodeGuard：测试、lint、构建、依赖与凭据检查，作为 `tests/static_analysis` 证据。
- CodeReview：基于正式规格和代码上下文输出语义风险，作为 `semantic_review` 证据。
- 机器 PASS 不自动成为用户验收；代码变化使可过期证据失效。

## 兼容模式

旧 `.flowguard/project.json` 与十阶段命令只用于已有项目迁移。仅当检测到旧状态或用户明确要求时，才路由到 `flowguard-requirements` 等阶段技能；新任务不得默认生成十份 `.flowguard` 规格。
