# AGENTS.md — flowgate-plugin 开发纪律

给 AI（与本仓开发者）的强制纪律。违反任何一条的提交都不应被合并。

## 全局约束（照 spec 决策表）

- 命名：仓库 `flowgate-plugin`、name `flowgate`、displayName「研发流程门禁」、i18n en "FlowGate: R&D Process Gate"、命令前缀 `/flowgate-*`、产物目录 `.flowgate/`。
- Python 仅标准库；测试用 `python3 -m unittest discover -s tests`（不是 pytest）。
- SKILL.md ≤ 500 行；frontmatter 必含 `name`（kebab，与目录同名）/ `license: Apache-2.0` / `description`（含触发词与负面边界）/ `compatibility`。
- 跨技能引用只用「技能名 + `npx skills add <org>/<pkg> --skill <name>`」，禁止 `../` 相对路径指向其它技能。
- 硬门禁唯一模式：无 strict_mode 软化开关；唯一逃生 = 用户发起的 override 且必须留痕；`accepted` 状态只能由用户确认写入，agent 不得自验收。
- REQ-ID 全局唯一，格式 `<feature-id>/REQ-<n>`；feature-id/模块名 kebab `^[a-z0-9]+(?:-[a-z0-9]+)*$`。
- 门禁/校验输出统一诊断信封 `{severity, code, message, fix}`（severity ∈ ERROR|WARNING|INFO）。
- 四宿主 manifest 版本字段必须一致（`.codex-plugin/plugin.json` 例外：`<v>+codex.<YYYYMMDD>`）；`.zcode-plugin/plugin.json` 不得含 `hooks` 键；不得含占位 `mcpServers`。
- 项目级产物增补一律追加式 + 来源标注（`feature: <id>`），禁止改写既有正文。
- LICENSE Apache-2.0 + `THIRD-PARTY-NOTICES.md` 必含 OpenSpec MIT 声明。
- 文档与 commit message 用中文。

## 发版纪律

任何代码改动——无论大小——都要 bump + 发版（`scripts/bump-plugin.mjs`，市场仓主本的分发副本）；市场端靠版本号感知更新。发布走 PR 合并 + tag `vX.Y.Z`。

## vendor 纪律（skills.lock.json / plugin-local-skills.json）

- 上游技能仓是事实源，本仓持校验和快照；受管技能**禁止在本仓直接编辑**。
- Tier 1 vendor 前提：上游仓有不可变 `vX.Y.Z` tag；无 tag 一律降 Tier 2 引用。
- 改上游 → 打不可变 tag → 更新 `skills.lock.json` → `python3 scripts/vendor/skill_vendor.py update`。
- `plugin-local-skills.json` 是本仓自研技能白名单；`skills/` 下未登记的目录会被 `check` 拒绝。

## 实现规格参照

- 设计文档（单一权威）：`docs/superpowers/specs/2026-09-22-devflow-plugin-design.md`
- Phase 1 实施计划：工作区 `docs/superpowers/plans/2026-09-22-flowgate-plugin-phase1.md`
- 钩子协议：`hooks/__protocol__.md`（改协议必须同 commit 更新契约与测试）
