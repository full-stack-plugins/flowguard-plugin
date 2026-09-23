# AGENTS.md — flowguard-plugin 开发纪律

给 AI（与本仓开发者）的强制纪律。违反任何一条的提交都不应被合并。

## 全局约束（照 spec 决策表）

- 命名：仓库 `flowguard-plugin`、name `flowguard`、displayName「研发流程门禁」、i18n en "FlowGuard: R&D Process Gate"、命令前缀 `/flowguard-*`。十阶段产物只写 `docs/project/` 与 `docs/features/<task-id>/`；新项目不得创建 `.flowguard/`。
- Python 仅标准库；测试用 `python3 -m unittest discover -s tests`（不是 pytest）。
- SKILL.md ≤ 500 行；frontmatter 必含 `name`（kebab，与目录同名）/ `license: Apache-2.0` / `description`（含触发词与负面边界）/ `compatibility`。
- 跨技能引用只用「技能名 + `npx skills add <org>/<pkg> --skill <name>`」，禁止 `../` 相对路径指向其它技能。
- 十阶段由智能体推进，Hook 只校验与拦截；门禁无 strict_mode 软化开关。用户批准与验收不得由 agent 伪造；旧状态仅供迁移和兼容读取。
- REQ-ID 全局唯一，格式 `<feature-id>/REQ-<n>`；feature-id/模块名 kebab `^[a-z0-9]+(?:-[a-z0-9]+)*$`。
- 门禁/校验输出统一诊断信封基础字段 `{severity, code, message, fix}`；新治理拒绝可追加 `missing/allowed_actions`。
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

## 三条核心实现纪律

- **治理核单一判定源**：发现/上下文/证据/门禁只存在于 flowguard_lib，hooks 与命令只是呈现面（JSON 与文本永不漂移）。
- **SKILL.md 是生成物**：改内容改 `scripts/templates/workflows.py` 模板源，再跑 `scripts/generate_skills.py`；parity 测试强制一致。
- **accepted 只能依据真实用户批准写入**：`stage advance` 是新流程入口；agent 永远不能代替用户验收。宿主若无不可伪造回执，不得宣称已建立对抗性强制门禁。

## 实现规格参照

- 当前规格（单一权威）：`docs/superpowers/specs/2026-09-23-flowguard-docs-ten-stage-governance.md`
- 当前实施计划：`docs/superpowers/plans/2026-09-23-flowguard-agent-driven-sdd-governance.md`
- v0.2 的“十阶段仅兼容”决策已被当前规格取代；旧 `.flowguard/` 仅是迁移输入，不得作为新任务默认产物。
- 钩子协议：`hooks/__protocol__.md`（改协议必须同 commit 更新契约与测试）
