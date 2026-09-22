# FlowGuard · 研发流程门禁

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
Hooks: SessionStart (status digest), PreToolUse (hard gate, exit 2), PostToolUse (artifact validation + rework degradation), Stop (next-step digest). Contract: [hooks/\_\_protocol\_\_.md](hooks/__protocol__.md).

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
