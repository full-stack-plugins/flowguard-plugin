"""SKILL.md 模板唯一源（SKILL.md 是生成物，parity 测试防漂移，照 OpenSpec 机制）。"""

# 每行路由格式：「技能 → 用途」
SKILL_SPECS = [
    {
        "name": "flowguard", "scope": "router", "stage": None, "artifact": None,
        "goal": "驱动智能体发现并遵循适用的 SDD 流程，用确定性证据防止绕过必要步骤。",
        "description": ("Git 项目的智能体 SDD 治理入口。在会话开始、目标仓库或任务范围变化、"
                        "开始写码、提交或发布前使用；发现 Spec Kit/OpenSpec/Superpowers 原生产物，"
                        "分类任务并绑定会话+worktree+变更上下文，检查批准、依赖和证据。"
                        "不复制规格正文，不自动初始化工具，也不以固定十阶段代替智能体判断。"),
        "routes": [
            "flowguard-requirements → 需求分析（01）",
            "flowguard-architecture → 架构设计（02，项目级）",
            "flowguard-solution → 技术方案（03）",
            "flowguard-testcases → 测试用例（04）",
            "flowguard-hld → 概要设计（05）",
            "flowguard-lld → 详细设计（06）",
            "flowguard-standards → 编码规范（07，项目级）",
            "flowguard-review → 代码审查（08）",
            "flowguard-docs → 文档生成（09）",
            "flowguard-release → 部署交付（10，项目级）",
            "codeguard-plugin 的 codeguard-* → lint 门禁/CVE/安全审查（npx skills add full-stack-plugins/codeguard）",
        ],
    },
    {
        "name": "flowguard-requirements", "scope": "feature", "stage": "requirements", "artifact": "01-requirements",
        "goal": "产出功能需求产物 01-requirements.md：用户故事 + <feature>/REQ-n + 可验收标准。",
        "description": ("需求分析阶段的编排技能。当用户要写需求/用户故事/功能规格、或把模糊想法变成可验收需求时使用；"
                        "以 current_feature 为工作对象，产出 Requirement/Scenario 结构化需求。"
                        "不要用它做架构选型或写测试用例（后续阶段职责）。"),
        "routes": [
            "ddd-domain-designer → 领域建模深水区（npx skills add full-stack-skills/ddd-skills --skill ddd-domain-designer）",
            "feature-design → 行为契约式需求（npx skills add full-stack-skills/design-skills --skill feature-design）",
        ],
    },
    {
        "name": "flowguard-architecture", "scope": "project", "stage": "architecture", "artifact": "02-architecture",
        "goal": "产出项目架构产物 02-architecture.md：选型 / ADR 追加式列表 / 模块边界。",
        "description": ("架构设计阶段（项目级，走一次）。当用户要定技术选型、写 ADR、划模块边界时使用；"
                        "ADR 一律追加式并标注来源功能，禁止改写既有条目。"
                        "不要用它写单个功能的技术方案（那是 flowguard-solution）。"),
        "routes": [
            "ddd-architecture-selector → 五种架构选型决策（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-selector）",
            "ddd-architecture-doc → C4 图/ADR 模板（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-doc）",
        ],
    },
    {
        "name": "flowguard-solution", "scope": "feature", "stage": "solution", "artifact": "03-solution",
        "goal": "产出功能技术方案 03-solution.md：实现选型 / 接口契约 / 风险清单。",
        "description": ("技术方案阶段。当用户为某功能定实现方案、接口契约或风险预案时使用。"
                        "不要用它做全项目架构决策（flowguard-architecture）。"),
        "routes": [
            "ddd-domain-designer → 方案中的领域建模（npx skills add full-stack-skills/ddd-skills --skill ddd-domain-designer）",
            "ddd-architecture-doc → 技术决策记录（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-doc）",
        ],
    },
    {
        "name": "flowguard-testcases", "scope": "feature", "stage": "testcases", "artifact": "04-testcases",
        "goal": "产出测试用例 04-testcases.md：用例 + 追溯矩阵（REQ↔用例↔测试文件）。",
        "description": ("测试用例阶段（厚阶段）。当用户要写测试用例、建追溯矩阵、或在写码前定测试计划时使用；"
                        "每条用例必须标注 REQ 与测试文件（TDD 门槛的机械检查依据）。"
                        "不要用它实际运行测试或写业务代码。"),
        "routes": [
            "ddd-testing-strategist → 测试策略/测试金字塔（npx skills add full-stack-skills/ddd-skills --skill ddd-testing-strategist）",
            "junit-mockito-patterns → Java 单测（npx skills add full-stack-skills/java-skills --skill junit-mockito-patterns）",
            "python-testing-patterns → pytest（npx skills add full-stack-skills/python-skills --skill python-testing-patterns）",
            "testing-skills 的 jest/vitest/playwright/cypress 等 → 前端/E2E 框架",
        ],
    },
    {
        "name": "flowguard-hld", "scope": "feature", "stage": "hld", "artifact": "05-hld",
        "goal": "产出概要设计 05-hld.md：模块/服务划分与交互。",
        "description": "概要设计阶段（薄）。当用户要划分模块/服务、描述交互与数据流时使用。不要用它写类级明细（flowguard-lld）。",
        "routes": [
            "ddd-architecture-selector → 架构模式参照（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-selector）",
            "ddd-architecture-doc → C4 图（npx skills add full-stack-skills/ddd-skills --skill ddd-architecture-doc）",
        ],
    },
    {
        "name": "flowguard-lld", "scope": "feature", "stage": "lld", "artifact": "06-lld",
        "goal": "产出详细设计 06-lld.md：类/表/接口明细与异常边界。",
        "description": "详细设计阶段（薄）。当用户要定类职责、表结构、接口字段时使用。不要用它重复概要设计的模块划分。",
        "routes": [
            "ddd-api-designer → API 设计（npx skills add full-stack-skills/ddd-skills --skill ddd-api-designer）",
            "codebase-design → 深模块设计（npx skills add full-stack-skills/agent-skills --skill codebase-design）",
        ],
    },
    {
        "name": "flowguard-standards", "scope": "project", "stage": "standards", "artifact": "07-standards",
        "goal": "产出项目编码规范集 07-standards.md：按模块栈路由规范来源，追加式增补。",
        "description": ("编码规范阶段（项目级，厚）。当用户要定编码规范、按栈选规范来源、或增补项目规约时使用；"
                        "规范集生成后，写码门禁才解锁。不要用它执行 lint（那是 codeguard-plugin）。"),
        "routes": [
            "java-development-manual → Java 规约（npx skills add full-stack-skills/java-skills --skill java-development-manual）",
            "java-conventions → Java 编码与注释（npx skills add full-stack-skills/java-skills --skill java-conventions）",
            "python-code-style → Python 风格（npx skills add full-stack-skills/python-skills --skill python-code-style）",
            "rust-style-clippy → Rust（npx skills add full-stack-skills/rust-skills --skill rust-style-clippy）",
            "codeguard-plugin → lint 门禁执行（npx skills add full-stack-plugins/codeguard）",
        ],
    },
    {
        "name": "flowguard-review", "scope": "feature", "stage": "review", "artifact": "08-review",
        "goal": "产出证据化代码审查报告 08-review.md：发现项（证据）+ 结论（fix/wontfix/deferred）。",
        "description": ("代码审查阶段（薄）。当用户要求审查某功能的代码变更、或汇总审查发现项时使用；"
                        "每条发现项必须带证据与结论。不要用它跑静态检查工具（codeguard-plugin 职责）。"),
        "routes": [
            "ddd-code-reviewer → DDD 架构审查（npx skills add full-stack-skills/ddd-skills --skill ddd-code-reviewer）",
            "rust-code-review / kotlin-code-review / swift-code-review / zig-code-review → 对应语言审查",
            "codeguard-security-code → 安全审查（npx skills add full-stack-plugins/codeguard）",
        ],
    },
    {
        "name": "flowguard-docs", "scope": "feature", "stage": "docs", "artifact": "09-docs",
        "goal": "产出功能文档清单与生成记录 09-docs.md。",
        "description": "文档生成阶段（薄）。当用户要为功能补 API/用户/运维文档并记录生成情况时使用。不要用它写发布清单（flowguard-release）。",
        "routes": [
            "full-stack-doc → 产品文档体系（npx skills add full-stack-skills/document-skills --skill full-stack-doc）",
            "api-doc-generator → API 文档（npx skills add full-stack-skills/document-skills --skill api-doc-generator）",
        ],
    },
    {
        "name": "flowguard-release", "scope": "project", "stage": "release", "artifact": "10-release",
        "goal": "产出发布清单 10-release.md：版本/校验和/回滚方案/证据。",
        "description": ("部署交付阶段（项目级收口）。当所有功能 done 后做交付收口、写发布清单时使用。"
                        "不要在还有 active 功能时尝试发布（门禁会阻断）。"),
        "routes": [
            "easy4j-deploy → 发布 SOP（npx skills add full-stack-skills/java-skills --skill easy4j-deploy）",
            "fw-release-gate → 发布门禁参照（npx skills add full-stack-skills/firmware-skills --skill fw-release-gate）",
            "codeguard-cve → 发布前 CVE 扫描（npx skills add full-stack-plugins/codeguard）",
        ],
    },
]


def _cli(name):
    return f'python3 "${{CLAUDE_PLUGIN_ROOT}}/scripts/flowguard_state.py"'


def render_skill(spec):
    """渲染单个 SKILL.md（统一骨架：frontmatter→目标→30秒开始→边界→模板→自检→验收→硬软分离）。"""
    name = spec["name"]
    if spec["scope"] == "router":
        return f"""---
name: {name}
license: Apache-2.0
description: {spec['description']}
compatibility: Python 3 标准库；Git 项目无需预先初始化 FlowGuard。原生 SDD 工具是否可用以 discover 结果为准。
---

# flowguard —— 智能体驱动的 SDD 治理

智能体负责语义判断和流程推进；Spec Kit、OpenSpec、Superpowers 提供原生规格与工程方法；FlowGuard 只保存治理元数据、校验证据并阻止绕过。

## 30 秒开始

```bash
{_cli(name)} discover --json
{_cli(name)} context show --session "$SESSION_ID" --json
{_cli(name)} governance --session "$SESSION_ID" --action code_write --json
```

## 智能体执行循环

1. **发现**：确认真实仓库/worktree、项目类型、项目指令、原生 SDD 标识、可用 CLI 和已有变更。
2. **定位**：判断 `read_only`、`simple_change`、`important_change` 或 `incident`，确认是已有变更、父功能、子功能还是实现任务。
3. **选择**：按“用户指定 → 项目指令 → 已有产物 → 已采用体系 → 默认规则”确定唯一规格事实源。
4. **绑定**：用 `context bind` 将会话 + worktree + task 绑定到原生规格引用；只保存引用，不复制正文。
5. **推进**：调用所选体系的真实命令或技能。Spec Kit/OpenSpec 管规格，Superpowers 管工程执行。
6. **验证**：运行真实测试、CodeGuard 静态检查和 CodeReview 语义审查，用 `evidence record` 绑定当前代码指纹。
7. **复核**：写码、`git commit`、发布前运行 `governance`；缺失时执行 `allowed_actions` 中的补救路径。
8. **恢复**：下一轮从 active 上下文、原生产物和有效证据继续，不重复生成已完成材料。

## 规格事实源选择

| 发现结果 | 行为 |
|:---|:---|
| 只有 `.specify/` | Spec Kit 是规格事实源 |
| 只有 `openspec/` | OpenSpec 是规格事实源 |
| 只有 Superpowers specs/plans | 延续 Superpowers 文档 |
| Spec Kit/OpenSpec + Superpowers | 前者管规格，后者管工程执行 |
| `.specify/` 与 `openspec/` 冲突 | 停止创建规格，请用户为本次变更选择 |
| 无体系 + simple/read-only | 不初始化完整 SDD |
| 无体系 + important Brownfield | 推荐 OpenSpec，说明文件影响后等待初始化批准 |
| 无体系 + important Greenfield | 推荐 Spec Kit，说明文件影响后等待初始化批准 |

## 必须由用户决定

- 首次 `specify init` / `openspec init`、工具安装升级或体系迁移。
- Spec Kit 与 OpenSpec 无法自动判定的冲突。
- 核心目标、非目标、验收标准和公共兼容范围变化。
- `scope_approved`、`user_acceptance` 和任何 override。

## 证据与插件分工

- FlowGuard：流程归属、前置条件、父子依赖、证据有效性和最终动作门禁。
- CodeGuard：测试、lint、构建、依赖与凭据检查，作为 `tests/static_analysis` 证据。
- CodeReview：基于正式规格和代码上下文输出语义风险，作为 `semantic_review` 证据。
- 机器 PASS 不自动成为用户验收；代码变化使可过期证据失效。

## 兼容模式

旧 `.flowguard/project.json` 与十阶段命令只用于已有项目迁移。仅当检测到旧状态或用户明确要求时，才路由到 `flowguard-requirements` 等阶段技能；新任务不得默认生成十份 `.flowguard` 规格。
"""


    aid, stage = spec["artifact"], spec["stage"]
    routes = "\n".join(f"- {r}" for r in spec["routes"])
    scope_note = ("项目级阶段：全项目走一次。" if spec["scope"] == "project"
                  else "功能级阶段：以 current_feature 为工作对象。")
    checklist = {
        "requirements": ["每条需求有 REQ-ID 与可验收标准", "正文含 SHALL/MUST", "每条至少 1 个 Scenario"],
        "testcases": ["每条 REQ 至少一条用例", "每条用例标注测试文件且文件存在", "用例含步骤与预期"],
        "standards": ["覆盖所有已注册模块的栈", "增补为追加式并标注来源功能"],
    }.get(stage, ["产物按模板元信息头填写完整", "内容与前置产物一致（追溯）"])
    checks = "\n".join(f"- [ ] {c}" for c in checklist)
    acceptance = {
        "requirements": "validate 无 ERROR：REQ 格式合法且全部归属本功能",
        "testcases": "validate 无 ERROR：REQ 全覆盖、测试文件全部存在",
        "standards": "规范集覆盖全部模块栈，用户确认验收",
    }.get(stage, "validate 无 ERROR 且用户确认验收")
    legacy_description = (
        "兼容模式，仅当项目已有旧 .flowguard 十阶段状态或用户明确要求旧流程时使用。"
        + spec["description"]
    )
    return f"""---
name: {name}
license: Apache-2.0
description: {legacy_description}
compatibility: 旧十阶段兼容层；需要项目已有 .flowguard/project.json，阶段推进经由编排核 CLI。
---

# {name} —— {spec['goal']}

> **兼容模式**：仅当项目已有旧 `.flowguard` 十阶段状态，或用户明确要求继续旧流程时使用。新任务先交给 `flowguard` 主技能发现并绑定原生 SDD 事实源。

{scope_note}

## 30 秒开始

```bash
{_cli(name)} next                       # 进入当前阶段并取回机读指令
{_cli(name)} instructions {aid} --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
{_cli(name)} validate --json            # 产物自检
```

## 产物

写入 `.flowguard/` 下 `{aid}` 对应产物，模板见 `references/templates/{aid}.md`。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

{routes}

## 自检清单

{checks}

## 验收条件

{acceptance}。验收由用户执行 /flowguard-advance 写入 accepted。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单（validate 机械检查）
- 回改已验收产物会触发下游阶段自动降级（journal 留痕）
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守 instructions 返回的 context/rules（约束，不是产物内容）
- 引用 Tier 2 执行技能时给出安装命令
"""
