---
name: flowguard-solution
license: Apache-2.0
description: 技术方案阶段。当用户为某功能定实现方案、接口契约或风险预案时使用。不要用它做全项目架构决策（flowguard-architecture）。
compatibility: Python 3 标准库；十阶段文档位于 docs/，无需项目 .flowguard/ 目录。
---

# flowguard-solution —— 产出功能技术方案 03-solution.md：实现选型 / 接口契约 / 风险清单。

> **流程定位**：先由 `flowguard` 主技能发现项目并绑定任务。本技能负责十阶段中的当前阶段；智能体组织工作，FlowGuard 校验依赖和验收。

功能级阶段：以已绑定的 task-id 为工作对象。

## 30 秒开始

先从当前宿主确认已安装 FlowGuard 的插件根目录：Codex 可查 `codex plugin list`，Kimi 可查 `/plugins info flowguard`，ZCode 查插件管理界面。将绝对路径设为 `FLOWGUARD_PLUGIN_ROOT`，并在同一次 Shell 调用中运行下面的命令；不要假设 Hook 专用环境变量在 Agent Shell 中也存在，更不能从目标项目猜测同名脚本。

```bash
FLOWGUARD_PLUGIN_ROOT="<已确认的插件绝对安装目录>"
test -f "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" || exit 1
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" stage status --task-id "$TASK_ID" --json
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" stage advance --task-id "$TASK_ID" --stage 03-solution --status in_progress --json
# 填写并自检 docs/features/<task-id>/03-solution.md 后，取得真实批准依据，再申请验收：
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" stage advance --task-id "$TASK_ID" --stage 03-solution --status accepted --approval-ref "$APPROVAL_REF" --json
```

## 产物

写入 `docs/features/<task-id>/03-solution.md`，模板见 `references/templates/03-solution.md`。保留原生规格在其原位置，仅在文档中引用。阶段元信息和证据登记同文保存。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

- ddd-domain-designer → 方案中的领域建模（npx skills add full-stack-skills/ddd-skills --skill ddd-domain-designer）
- ddd-architecture-doc → 技术决策记录（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-doc）

## 自检清单

- [ ] 产物按模板元信息头填写完整
- [ ] 内容与前置产物一致（追溯）

## 验收条件

validate 无 ERROR 且用户确认验收。真实用户批准或可审计的继承/跳过依据不可由模型自述伪造；通过 `stage advance` 记录阶段状态。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单；`stage advance` 会检查已实现的机械约束
- 回改已验收产物会使本阶段验收指纹失效，应检查并重验受影响的后续阶段
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守主技能的任务上下文、原生规格和用户批准边界
- 引用 Tier 2 执行技能时给出安装命令
