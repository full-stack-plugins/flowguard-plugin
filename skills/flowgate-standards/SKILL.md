---
name: flowgate-standards
license: Apache-2.0
description: 编码规范阶段（项目级，厚）。当用户要定编码规范、按栈选规范来源、或增补项目规约时使用；规范集生成后，写码门禁才解锁。不要用它执行 lint（那是 codeguard-plugin）。
compatibility: 需要项目内已运行 /flowgate-init 且存在 current_feature（项目级阶段除外）；阶段推进经由编排核 CLI。
---

# flowgate-standards —— 产出项目编码规范集 07-standards.md：按模块栈路由规范来源，追加式增补。

项目级阶段：全项目走一次。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" next                       # 进入当前阶段并取回机读指令
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" instructions 07-standards --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" validate --json            # 产物自检
```

## 产物

写入 `.flowgate/` 下 `07-standards` 对应产物，模板见 `references/templates/07-standards.md`。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

- java-development-manual → Java 规约（npx skills add full-stack-skills/java-skills --skill java-development-manual）
- java-conventions → Java 编码与注释（npx skills add full-stack-skills/java-skills --skill java-conventions）
- python-code-style → Python 风格（npx skills add full-stack-skills/python-skills --skill python-code-style）
- rust-style-clippy → Rust（npx skills add full-stack-skills/rust-skills --skill rust-style-clippy）
- codeguard-plugin → lint 门禁执行（npx skills add full-stack-plugins/codeguard）

## 自检清单

- [ ] 覆盖所有已注册模块的栈
- [ ] 增补为追加式并标注来源功能

## 验收条件

规范集覆盖全部模块栈，用户确认验收。验收由用户执行 /flowgate-advance 写入 accepted。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单（validate 机械检查）
- 回改已验收产物会触发下游阶段自动降级（journal 留痕）
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守 instructions 返回的 context/rules（约束，不是产物内容）
- 引用 Tier 2 执行技能时给出安装命令
