# FlowGuard · 智能体 SDD 治理门禁

[![skills-check](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml/badge.svg)](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

FlowGuard 是面向 Codex、ZCode、Kimi 与 Claude 的智能体研发治理插件：**强制十阶段由智能体推进；原生 SDD 工具提供规格与方法；FlowGuard 用 `docs/` 文档、批准、依赖和证据防止跳过必要步骤。**

## 核心定位

- Spec Kit / OpenSpec：规格事实源，正式正文留在原生目录。
- Superpowers：需求澄清、计划、TDD、调试、审查和完成前验证方法。
- FlowGuard：发现项目现状，绑定 `会话 + worktree + 任务/变更`，校验父子依赖和证据，拦截不合规写码、提交与发布。
- CodeGuard：提供测试、静态分析、构建、依赖和凭据检查证据。
- CodeReview：提供结合规格和代码上下文的语义审查证据。

FlowGuard 不复制规格、不自动初始化工具，也不把机器 PASS 变成用户验收。

## 工作方式

```mermaid
flowchart LR
    D[发现 Git / SDD] --> C[智能体分类与选择]
    C --> B[绑定上下文]
    B --> N[智能体推进十阶段 docs 文档与原生规格]
    N --> E[测试 / CodeGuard / CodeReview]
    E --> G[FlowGuard 动作裁决]
    G -->|缺失| C
    G -->|满足| A[允许写码 / commit / release]
```

十阶段是可验证的流程骨架，不由 Hook 自动推进。只读任务只做发现和分类；需要写码的任务按适用范围完成十阶段门禁：

| 任务 | 默认治理 |
|:---|:---|
| 只读分析 | 完成发现和分类，不要求初始化 |
| 简单修改 | 绑定上下文，复用或有依据地跳过不适用阶段，保留验证证据 |
| 重要变更 | 绑定原生规格、完成十阶段产物与必要批准，按 TDD 推进 |
| 生产故障 | 允许先恢复稳定，行为变化随后补规格 |

## 快速开始

```bash
# 1. 只读发现：不会安装或初始化任何工具
/flowguard-discover

# 2. 智能体分类后绑定本次任务
/flowguard-context

# 3. 实施过程中记录真实证据
/flowguard-evidence

# 4. 写码、提交或发布前复核
/flowguard-governance
```

Kimi 将同源命令注册为带命名空间的 Markdown 命令，例如 `/flowguard:flowguard-discover`。`kimi-commands/` 由 `commands/*.json` 机械生成；修改 JSON 后运行 `python3 scripts/generate_kimi_commands.py --write`。若 Kimi Shell 未提供 `KIMI_PLUGIN_ROOT`，先通过 `/plugins info flowguard` 确认已启用插件的安装目录，再运行其自带 CLI。插件仍由 `full-stack-plugins` 统一登记与发布管理，源码仓库独立维护。

对应 CLI：

```bash
python3 scripts/flowguard_state.py discover --json
python3 scripts/flowguard_state.py context bind \
  --session session-1 --task-id refund-idempotency \
  --task-type important_change --spec-system openspec \
  --spec-ref openspec/changes/refund-idempotency --json
python3 scripts/flowguard_state.py stage status --task-id refund-idempotency --json
python3 scripts/flowguard_state.py governance \
  --session session-1 --action code_write --json
```

## 动作门禁

| 动作 | 最低条件 |
|:---|:---|
| 读取 / 补规格 | 保持开放，确保能解除阻断 |
| 补测试 | 已绑定治理上下文 |
| 写业务代码 | 01—07 阶段满足；重要变更另需有效规格与范围批准 |
| `git commit` | 01—09 阶段满足，且当前指纹的测试、静态分析、语义审查证据有效 |
| 发布 | 十阶段满足；10 发布清单所列功能的 09 文档仍有效，且发布就绪、用户验收、依赖/子任务收敛 |

拒绝使用 exit 2，并返回 `code / message / fix / missing / allowed_actions`。Hook 故障本身 fail-open；确定性治理缺口 fail-closed。

## 五类 Hooks

- `SessionStart`：只读发现项目和 SDD 状态，恢复上下文。
- `UserPromptSubmit`：提醒智能体重新判断任务、范围与事实源。
- `PreToolUse`：校验写码、Git commit、发布，并保护治理状态。
- `PostToolUse`：使旧证据过期；仅对明确执行测试的命令观察 exit code。CodeGuard/CodeReview 的 PASS 不能只凭退出码，仍需结构化、可核验的结果。
- Kimi 的 Shell `PostToolUseFailure`：明确的测试工具失败记 FAIL，避免旧 PASS 继续作为最新证据。
- `Stop`：汇总缺失证据和下一步，不把本轮结束当成任务完成。

协议见 [hooks/__protocol__.md](hooks/__protocol__.md)。

## 文档位置与旧项目迁移

项目级 02/07/10 放在 `docs/project/`，功能级 01/03/04/05/06/08/09 放在 `docs/features/<task-id>/`。新项目不创建 `.flowguard/`；会话缓存保存在宿主状态目录。旧项目先运行 `migrate --dry-run`，确认无冲突后再 `migrate --apply`，核对完成前保留旧数据。迁移中途失败时，已创建文档保留并在错误中列出，需人工核对；不会为了回滚而删除可能已被他人修改的文件。`legacy-init` 仅供旧命令兼容。

## 文档

- [FlowGuard-Architecture.zh_CN.md](docs/FlowGuard-Architecture.zh_CN.md) — 当前架构、运行流、可信边界和风险
- [十阶段 docs 治理规格](docs/superpowers/specs/2026-09-23-flowguard-docs-ten-stage-governance.md)
- [实施计划](docs/superpowers/plans/2026-09-23-flowguard-agent-driven-sdd-governance.md)
- [旧产物兼容契约](docs/FLOWGUARD_ARTIFACT_SPEC.md)
- [路线图](docs/roadmap.md)

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 scripts/vendor/skill_vendor.py check --offline
python3 scripts/generate_skills.py
python3 scripts/generate_kimi_commands.py
git diff --check
```

Python 仅使用标准库。许可证为 Apache-2.0；第三方参照见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
