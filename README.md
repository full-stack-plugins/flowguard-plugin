# FlowGuard · Agent-Driven SDD Governance

[![skills-check](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml/badge.svg)](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

FlowGuard is an agent governance plugin for Codex, ZCode, Kimi, and Claude. **The agent decides how to advance the task; native SDD tools own specifications and engineering methods; FlowGuard prevents required context, approvals, dependencies, and evidence from being skipped.**

## Responsibilities

- Spec Kit / OpenSpec own the native specification source of truth.
- Superpowers provides execution methods such as clarification, planning, TDD, debugging, review, and verification.
- FlowGuard discovers repository state, binds `session + worktree + task/change`, validates dependencies and evidence, and gates code writes, commits, and releases.
- CodeGuard produces deterministic test, static-analysis, build, dependency, and credential evidence.
- CodeReview produces semantic-review evidence grounded in the selected specification and code context.

FlowGuard does not copy specifications, silently initialize tools, or turn a machine PASS into user acceptance.

## Governance loop

```mermaid
flowchart LR
    D[Discover Git / SDD] --> C[Agent classifies and selects]
    C --> B[Bind context]
    B --> N[Advance native specs and implementation]
    N --> E[Tests / CodeGuard / CodeReview]
    E --> G[FlowGuard action decision]
    G -->|Missing| C
    G -->|Satisfied| A[Allow code / commit / release]
```

The required rule is “follow the applicable process,” not “run every task through a fixed pipeline.”

| Task type | Default governance |
|:---|:---|
| Read-only analysis | Discover and classify; no initialization required |
| Simple change | Lightweight context plus current-fingerprint verification |
| Important change | Bind a native specification, capture required approval, execute with TDD |
| Production incident | Restore stability first; backfill behavior-changing specifications |

## Quick start

```bash
/flowguard-discover    # read-only; never installs or initializes tools
/flowguard-context     # classify and bind this session/worktree/task
/flowguard-evidence    # record real verification evidence
/flowguard-governance  # check code-write, commit, or release readiness
```

CLI example:

```bash
python3 scripts/flowguard_state.py discover --json
python3 scripts/flowguard_state.py context bind \
  --session session-1 --task-id refund-idempotency \
  --task-type important_change --spec-system openspec \
  --spec-ref openspec/changes/refund-idempotency --json
python3 scripts/flowguard_state.py governance \
  --session session-1 --action code_write --json
```

## Action gates

| Action | Minimum condition |
|:---|:---|
| Read / specification remediation | Always open so a block can be resolved |
| Test write | Active governance context |
| Business-code write | Writable task; important changes also need a valid spec and scope approval |
| `git commit` | Current-fingerprint tests, static analysis, and semantic review |
| Release | Commit conditions plus release readiness, user acceptance, and completed dependencies/children |

Denials use exit code 2 and return `code / message / fix / missing / allowed_actions`. Hook failures fail open; known governance gaps fail closed.

## Hooks

- `SessionStart`: discover SDD state and restore context.
- `UserPromptSubmit`: remind the agent to reassess task, scope, and source of truth.
- `PreToolUse`: gate code writes, Git commits, and releases; protect governance state.
- `PostToolUse`: expire stale evidence and observe explicit test/check exit codes.
- `Stop`: summarize missing evidence and the next action without treating the turn as task completion.

See [hooks/__protocol__.md](hooks/__protocol__.md).

## Legacy compatibility

The v0.1 ten-stage `.flowguard` artifacts and commands remain available for existing projects. They are compatibility-only: new tasks no longer create ten specification copies or rely on one global `current_feature`.

## Documentation

- [Current architecture](docs/FlowGuard-Architecture.zh_CN.md)
- [Agent-driven SDD governance specification](docs/superpowers/specs/2026-09-23-flowguard-agent-driven-sdd-governance.md)
- [Implementation plan](docs/superpowers/plans/2026-09-23-flowguard-agent-driven-sdd-governance.md)
- [Legacy artifact contract](docs/FLOWGUARD_ARTIFACT_SPEC.md)
- [Roadmap](docs/roadmap.md)

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 scripts/vendor/skill_vendor.py check --offline
python3 scripts/generate_skills.py
git diff --check
```

Python standard library only. Apache-2.0; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for implementation references.
