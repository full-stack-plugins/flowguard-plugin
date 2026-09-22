---
name: flowguard-testcases
license: Apache-2.0
description: 测试用例阶段（厚阶段）。当用户要写测试用例、建追溯矩阵、或在写码前定测试计划时使用；每条用例必须标注 REQ 与测试文件（TDD 门槛的机械检查依据）。不要用它实际运行测试或写业务代码。
compatibility: 需要项目内已运行 /flowguard-init 且存在 current_feature（项目级阶段除外）；阶段推进经由编排核 CLI。
---

# flowguard-testcases —— 产出测试用例 04-testcases.md：用例 + 追溯矩阵（REQ↔用例↔测试文件）。

功能级阶段：以 current_feature 为工作对象。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" next                       # 进入当前阶段并取回机读指令
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" instructions 04-testcases --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" validate --json            # 产物自检
```

## 产物

写入 `.flowguard/` 下 `04-testcases` 对应产物，模板见 `references/templates/04-testcases.md`。

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

validate 无 ERROR：REQ 全覆盖、测试文件全部存在。验收由用户执行 /flowguard-advance 写入 accepted。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单（validate 机械检查）
- 回改已验收产物会触发下游阶段自动降级（journal 留痕）
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守 instructions 返回的 context/rules（约束，不是产物内容）
- 引用 Tier 2 执行技能时给出安装命令
