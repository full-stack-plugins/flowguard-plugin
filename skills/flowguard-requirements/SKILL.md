---
name: flowguard-requirements
license: Apache-2.0
description: 兼容模式，仅当项目已有旧 .flowguard 十阶段状态或用户明确要求旧流程时使用。需求分析阶段的编排技能。当用户要写需求/用户故事/功能规格、或把模糊想法变成可验收需求时使用；以 current_feature 为工作对象，产出 Requirement/Scenario 结构化需求。不要用它做架构选型或写测试用例（后续阶段职责）。
compatibility: 旧十阶段兼容层；需要项目已有 .flowguard/project.json，阶段推进经由编排核 CLI。
---

# flowguard-requirements —— 产出功能需求产物 01-requirements.md：用户故事 + <feature>/REQ-n + 可验收标准。

> **兼容模式**：仅当项目已有旧 `.flowguard` 十阶段状态，或用户明确要求继续旧流程时使用。新任务先交给 `flowguard` 主技能发现并绑定原生 SDD 事实源。

功能级阶段：以 current_feature 为工作对象。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" next                       # 进入当前阶段并取回机读指令
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" instructions 01-requirements --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" validate --json            # 产物自检
```

## 产物

写入 `.flowguard/` 下 `01-requirements` 对应产物，模板见 `references/templates/01-requirements.md`。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

- ddd-domain-designer → 领域建模深水区（npx skills add full-stack-skills/ddd-skills --skill ddd-domain-designer）
- feature-design → 行为契约式需求（npx skills add full-stack-skills/design-skills --skill feature-design）

## 自检清单

- [ ] 每条需求有 REQ-ID 与可验收标准
- [ ] 正文含 SHALL/MUST
- [ ] 每条至少 1 个 Scenario

## 验收条件

validate 无 ERROR：REQ 格式合法且全部归属本功能。验收由用户执行 /flowguard-advance 写入 accepted。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单（validate 机械检查）
- 回改已验收产物会触发下游阶段自动降级（journal 留痕）
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守 instructions 返回的 context/rules（约束，不是产物内容）
- 引用 Tier 2 执行技能时给出安装命令
