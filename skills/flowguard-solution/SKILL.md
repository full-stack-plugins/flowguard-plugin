---
name: flowguard-solution
license: Apache-2.0
description: 兼容模式，仅当项目已有旧 .flowguard 十阶段状态或用户明确要求旧流程时使用。技术方案阶段。当用户为某功能定实现方案、接口契约或风险预案时使用。不要用它做全项目架构决策（flowguard-architecture）。
compatibility: 旧十阶段兼容层；需要项目已有 .flowguard/project.json，阶段推进经由编排核 CLI。
---

# flowguard-solution —— 产出功能技术方案 03-solution.md：实现选型 / 接口契约 / 风险清单。

> **兼容模式**：仅当项目已有旧 `.flowguard` 十阶段状态，或用户明确要求继续旧流程时使用。新任务先交给 `flowguard` 主技能发现并绑定原生 SDD 事实源。

功能级阶段：以 current_feature 为工作对象。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" next                       # 进入当前阶段并取回机读指令
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" instructions 03-solution --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" validate --json            # 产物自检
```

## 产物

写入 `.flowguard/` 下 `03-solution` 对应产物，模板见 `references/templates/03-solution.md`。

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

validate 无 ERROR 且用户确认验收。验收由用户执行 /flowguard-advance 写入 accepted。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单（validate 机械检查）
- 回改已验收产物会触发下游阶段自动降级（journal 留痕）
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守 instructions 返回的 context/rules（约束，不是产物内容）
- 引用 Tier 2 执行技能时给出安装命令
