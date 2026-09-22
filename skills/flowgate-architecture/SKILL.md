---
name: flowgate-architecture
license: Apache-2.0
description: 架构设计阶段（项目级，走一次）。当用户要定技术选型、写 ADR、划模块边界时使用；ADR 一律追加式并标注来源功能，禁止改写既有条目。不要用它写单个功能的技术方案（那是 flowgate-solution）。
compatibility: 需要项目内已运行 /flowgate-init 且存在 current_feature（项目级阶段除外）；阶段推进经由编排核 CLI。
---

# flowgate-architecture —— 产出项目架构产物 02-architecture.md：选型 / ADR 追加式列表 / 模块边界。

项目级阶段：全项目走一次。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" next                       # 进入当前阶段并取回机读指令
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" instructions 02-architecture --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" validate --json            # 产物自检
```

## 产物

写入 `.flowgate/` 下 `02-architecture` 对应产物，模板见 `references/templates/02-architecture.md`。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

- ddd-architecture-selector → 五种架构选型决策（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-selector）
- ddd-architecture-doc → C4 图/ADR 模板（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-doc）

## 自检清单

- [ ] 产物按模板元信息头填写完整
- [ ] 内容与前置产物一致（追溯）

## 验收条件

validate 无 ERROR 且用户确认验收。验收由用户执行 /flowgate-advance 写入 accepted。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单（validate 机械检查）
- 回改已验收产物会触发下游阶段自动降级（journal 留痕）
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守 instructions 返回的 context/rules（约束，不是产物内容）
- 引用 Tier 2 执行技能时给出安装命令
