---
name: flowguard
license: Apache-2.0
description: Git 项目的智能体 SDD 治理入口。在会话开始、目标仓库或任务范围变化、开始写码、提交或发布前使用；发现 Spec Kit/OpenSpec/Superpowers 原生产物，分类任务并绑定会话+worktree+变更上下文，推进 docs/ 中的强制十阶段，检查批准、依赖和证据；不复制原生规格正文，不自动初始化工具。
compatibility: Python 3 标准库；Git 项目无需预先初始化 FlowGuard。原生 SDD 工具是否可用以 discover 结果为准。
---

# flowguard —— 智能体驱动的十阶段 SDD 治理

十阶段是强制流程骨架，不是由 Hook 自动推进的固定脚本。智能体判断任务及下一步，Spec Kit/OpenSpec 管正式规格，Superpowers 管工程方法；FlowGuard 校验 `docs/` 中的阶段产物、批准和证据，并阻止绕过。

项目级文档位于 `docs/project/`（02、07、10）；功能及独立子功能位于 `docs/features/<task-id>/`（01、03、04、05、06、08、09）。原生规格只在阶段文档中引用，不复制正文。

## 30 秒开始

先从当前宿主确认已安装 FlowGuard 的插件根目录：Codex 可查 `codex plugin list`，Kimi 可查 `/plugins info flowguard`，ZCode 查插件管理界面。将绝对路径设为 `FLOWGUARD_PLUGIN_ROOT`，并在同一次 Shell 调用中运行下面的命令；不要假设 Hook 专用环境变量在 Agent Shell 中也存在，更不能从目标项目猜测同名脚本。

```bash
FLOWGUARD_PLUGIN_ROOT="<已确认的插件绝对安装目录>"
test -f "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" || exit 1
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" discover --json
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" context bind --session "$SESSION_ID" --task-id "$TASK_ID" --task-type important_change --spec-system openspec --spec-ref openspec/changes/example/proposal.md --json
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" stage status --task-id "$TASK_ID" --json
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" context show --session "$SESSION_ID" --json
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" governance --session "$SESSION_ID" --action code_write --json
```

## 智能体执行循环

1. **发现**：确认真实仓库/worktree、项目类型、项目指令、原生 SDD 标识、可用 CLI 和已有变更。
2. **定位**：判断 `read_only`、`simple_change`、`important_change` 或 `incident`，确认是已有变更、父功能、子功能还是实现任务。
3. **选择**：按“用户指定 → 项目指令 → 已有产物 → 已采用体系 → 默认规则”确定唯一规格事实源。
4. **绑定**：用 `context bind` 将会话 + worktree + task 绑定到原生规格引用；创建缺失的十阶段文档，不复制规格正文。
5. **推进**：用 `stage status` 找到首个未满足阶段，调用对应阶段技能及原生工具，补文档、验证并通过 `stage advance` 显式推进；项目级阶段复用，不为子功能复制。
6. **验证**：运行真实测试、CodeGuard 静态检查和 CodeReview 语义审查，用 `evidence record` 绑定当前代码指纹。
7. **复核**：写码、`git commit`、发布前运行 `governance`；缺失时执行 `allowed_actions` 中的补救路径。
8. **恢复**：下一轮从 `docs/`、原生产物和有效证据恢复阶段；会话缓存丢失时重新绑定，不重复生成已完成材料。

阶段状态及验收来自 `docs/`，不能用模型自述代替用户批准。阶段正文改变后，既有验收失效。01—07 满足后才写业务代码；提交还需 08—09 和有效检查证据；发布还需 10、用户验收及子任务完成。读取、补规格和补测试始终可用。

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

