"""SKILL.md 模板唯一源（SKILL.md 是生成物，parity 测试防漂移，照 OpenSpec 机制）。"""

# 每行路由格式：「技能 → 用途」
SKILL_SPECS = [
    {
        "name": "flowguard", "scope": "router", "stage": None, "artifact": None,
        "goal": "把研发流程意图路由到正确的阶段技能或执行技能，不亲自实现任何阶段产物。",
        "description": ("flowguard 研发流程门禁的路由中心。当用户提到流程/阶段/验收/门禁/推进、"
                        "或不确定该用哪个 flowguard-* 技能时使用；按意图把工作路由到十个阶段技能，"
                        "lint/CVE/安全等治理需求路由给 codeguard-plugin。"
                        "不要用它直接编写需求或测试用例（那是阶段技能的职责）。"),
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
        routes = "\n".join(f"- {r}" for r in spec["routes"])
        return f"""---
name: {name}
license: Apache-2.0
description: {spec['description']}
compatibility: 需要项目内已运行 /flowguard-init；所有状态查询经由编排核 CLI，只读。
---

# flowguard —— 研发流程门禁 · 路由中心

把研发流程意图路由到正确的阶段技能或执行技能。流水线：需求分析 → 架构设计 → 技术方案 → 测试用例 → 概要设计 → 详细设计 → 编码规范 → 代码审查 → 文档生成 → 部署交付（十阶段）。

## 30 秒开始

```bash
{_cli(name)} status        # 流程看板
{_cli(name)} gate          # 四类动作放行状态
```

## REQUIRED ROUTER

{routes}

## 流程操作入口（命令）

/flowguard-init · /flowguard-feature · /flowguard-next · /flowguard-advance · /flowguard-gate · /flowguard-override

## 硬性约束（会被门禁/校验强制）

- 写业务源码前：需求/方案/用例/概设/详设全部 accepted（TDD 门槛），项目规范已生成
- 验收（accepted）只能由用户确认写入；override 必须用户发起 + 理由留痕
- 状态只能经编排核 CLI 变更；手改 state.json 视为破坏

## 软约束（prompt 级契约，靠执行者自觉）

- 产物遵守模板与元信息头；项目级产物增补一律追加式
- 跨技能引用只用「技能名 + 安装命令」
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
    return f"""---
name: {name}
license: Apache-2.0
description: {spec['description']}
compatibility: 需要项目内已运行 /flowguard-init 且存在 current_feature（项目级阶段除外）；阶段推进经由编排核 CLI。
---

# {name} —— {spec['goal']}

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


def render_artifact_template(artifact_id, body_ctx):
    from . import artifacts
    return artifacts.render(artifact_id, body_ctx)
