# FlowGuard · 研发流程门禁

[![skills-check](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml/badge.svg)](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Four-host plugin (ZCode / Codex / Kimi / Claude) that orchestrates the full SDLC as a **ten-stage pipeline with hard stage gates**: Requirements → Architecture → Solution → Test Cases → HLD → LLD → Coding Standards → Code Review → Docs → Release.

## Positioning

flowguard is a **process orchestrator**, not a toolbox: it manages stage progression, artifact hand-offs and gate enforcement for multiple features across multiple modules. Inspiration: [OpenSpec](https://github.com/Fission-AI/OpenSpec) (MIT) — see THIRD-PARTY-NOTICES.md.

## At a glance

- **Ten stages**, each producing a traceable artifact under `.flowguard/`
- **Three-level model**: project-level stages (architecture / standards / release) run once; feature-level pipelines (requirements → solution → testcases → hld → lld → review → docs) run per feature, in parallel; modules annotate code ownership
- **Hard gates**: writing business code requires accepted requirements+solution+testcases+hld+lld (TDD gate) and generated standards; PreToolUse hook blocks with `exit 2` and a diagnostic envelope `{severity, code, message, fix}`
- **Human-in-the-loop**: `accepted` can only be written by the user (`/flowguard-advance`); the only escape is a user-initiated, journaled `/flowguard-override`
- **Traceability**: every test case references its REQ id and its test file; coverage is checked mechanically

## Quick start

```bash
# in your project root
/flowguard-init                                     # scaffold .flowguard/, detect stack & modules
/flowguard-feature new order-refund --modules order # declare a feature and its modules
/flowguard-next                                     # start the current stage, get machine-read instructions
# ... produce the stage artifact (skill routes to executors) ...
/flowguard-advance                                  # user acceptance -> accepted
```

AI entry points: `/flowguard-status`, `/flowguard-gate`, `/flowguard-override` (journaled escape hatch).

## Commands & Hooks

Commands: `/flowguard-init | -feature | -status | -next | -advance | -gate | -override`.

CLI subcommands (`python3 scripts/flowguard_state.py <cmd>`, exit codes: 0 ok / 2 gate-blocked / 3 error):

| subcommand | 作用 |
|---|---|
| `init` | 建 `.flowgate/` 骨架（幂等） |
| `status [--feature X]` | 流程看板（单功能详情用 --feature） |
| `feature new <id> --modules <m...>` / `list` / `done` / `drop --reason R` | 功能生命周期 |
| `next [--feature X \| --stage S]` | 开始阶段并取回机读指令 |
| `advance [--feature X] [--stage S]` | 用户验收（accepted 唯一写入点） |
| `override --reason R [...]` | 留痕逃生 |
| `gate [--action A --path P]` | 门禁自检 / 定向判定 |
| `validate [--feature X]` | 产物机械校验 |
| `instructions <artifact> [--feature X]` | 阶段指令（context/rules/模板/Tier2） |
Hooks: SessionStart (status digest), PreToolUse (hard gate, exit 2), PostToolUse (artifact validation + rework degradation), Stop (next-step digest). Contract: [hooks/\_\_protocol\_\_.md](hooks/__protocol__.md).

## Docs

- [docs/architecture.md](docs/architecture.md) — 架构（四层/三级模型/门禁）
- [docs/FLOWGUARD_ARTIFACT_SPEC.md](docs/FLOWGUARD_ARTIFACT_SPEC.md) — 产物格式契约（十类产物 + 占位符规则）
- [docs/roadmap.md](docs/roadmap.md) — Phase 2/3 路线图与开放问题

## Verification

```bash
python3 -m unittest discover -s tests            # state machine, gate matrix, hooks, parity...
python3 scripts/vendor/skill_vendor.py check --offline
python3 scripts/generate_skills.py && git diff --exit-code skills/
```

## Compatibility

ZCode (convention-based hook discovery), Kimi (inline hooks manifest), Codex & Claude (`hooks/hooks.json`). POSIX only (fcntl lock). Python stdlib only.

## License

Apache-2.0. OpenSpec (MIT) implementation reference — see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Related skills: install executors via `npx skills add full-stack-skills/<pkg> --skill <name>`; lint governance via `npx skills add full-stack-plugins/codeguard`.
