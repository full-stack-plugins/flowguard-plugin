---
name: flowgate-hld
license: Apache-2.0
description: 概要设计阶段（薄）。当用户要划分模块/服务、描述交互与数据流时使用。不要用它写类级明细（flowgate-lld）。
compatibility: 需要项目内已运行 /flowgate-init 且存在 current_feature（项目级阶段除外）；阶段推进经由编排核 CLI。
---

# flowgate-hld —— 产出概要设计 05-hld.md：模块/服务划分与交互。

功能级阶段：以 current_feature 为工作对象。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" next                       # 进入当前阶段并取回机读指令
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" instructions 05-hld --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" validate --json            # 产物自检
```

## 产物

写入 `.flowgate/` 下 `05-hld` 对应产物，模板见 `references/templates/05-hld.md`。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

- ddd-architecture-selector → 架构模式参照（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-selector）
- ddd-architecture-doc → C4 图（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-doc）

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
