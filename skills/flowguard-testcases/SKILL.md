---
name: flowguard-testcases
license: Apache-2.0
description: 测试用例阶段（厚阶段）。当用户要写测试用例、建追溯矩阵、或在写码前定测试计划时使用；每条用例必须标注 REQ 与测试文件（TDD 门槛的机械检查依据）。不要用它实际运行测试或写业务代码。
compatibility: Python 3 标准库；十阶段文档位于 docs/。
---

# flowguard-testcases —— 产出测试用例 04-testcases.md：用例 + 追溯矩阵（REQ↔用例↔测试文件）。

> **流程定位**：先由 `flowguard` 主技能发现项目并绑定任务。本技能负责十阶段中的当前阶段；智能体组织工作，FlowGuard 校验依赖和验收。

功能级阶段：以已绑定的 task-id 为工作对象。

## 30 秒开始

先从当前宿主确认已安装 FlowGuard 的插件根目录：Codex 可查 `codex plugin list`，Kimi 可查 `/plugins info flowguard`，ZCode 查插件管理界面。将绝对路径设为 `FLOWGUARD_PLUGIN_ROOT`，并在同一次 Shell 调用中运行下面的命令；不要假设 Hook 专用环境变量在 Agent Shell 中也存在，更不能从目标项目猜测同名脚本。

```bash
FLOWGUARD_PLUGIN_ROOT="<已确认的插件绝对安装目录>"
test -f "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" || exit 1
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" stage status --task-id "$TASK_ID" --json
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" stage advance --task-id "$TASK_ID" --stage 04-testcases --status in_progress --json
# 填写并自检 docs/features/<task-id>/04-testcases.md 后，取得真实批准依据，再申请验收：
python3 "${FLOWGUARD_PLUGIN_ROOT:?}/scripts/flowguard_state.py" stage advance --task-id "$TASK_ID" --stage 04-testcases --status accepted --approval-ref "$APPROVAL_REF" --json
```

## 产物

写入 `docs/features/<task-id>/04-testcases.md`，模板见 `references/templates/04-testcases.md`。保留原生规格在其原位置，仅在文档中引用。阶段元信息和证据登记同文保存。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

- ddd-testing-strategist → 测试策略/测试金字塔（npx skills add full-stack-skills/ddd-skills --skill ddd-testing-strategist）
- junit-mockito-patterns → Java 单测（npx skills add full-stack-skills/java-skills --skill junit-mockito-patterns）
- python-testing-patterns → pytest（npx skills add full-stack-skills/python-skills --skill python-testing-patterns）
- testing-skills 的 jest/vitest/playwright/cypress 等 → 前端/E2E 框架

## 自检清单

- [ ] 每条 REQ 至少一条用例
- [ ] 每条用例标注测试文件且文件存在
- [ ] 用例含步骤与预期

## 验收条件

validate 无 ERROR：REQ 全覆盖、测试文件全部存在。真实用户批准或可审计的继承/跳过依据不可由模型自述伪造；通过 `stage advance` 记录阶段状态。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单；`stage advance` 会检查已实现的机械约束
- 回改已验收产物会使本阶段验收指纹失效，应检查并重验受影响的后续阶段
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守主技能的任务上下文、原生规格和用户批准边界
- 引用 Tier 2 执行技能时给出安装命令
