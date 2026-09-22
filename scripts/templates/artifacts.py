"""产物模板（10 份）与 init 骨架生成。

格式基础：full-stack-doc v3.0（npx skills add full-stack-skills/document-skills --skill full-stack-doc）
—— 通用文档头/尾结构（SKILL §5.2）+ 格式约定（§5.3：章节编号/表格左对齐/状态标记/中英混排空格）+ 双花括号占位符。
机器校验标记（### Requirement: / #### Scenario: / - REQ: / - 测试文件: / ### 用例 / ### 发现）为校验契约，保持不变。
"""
from pathlib import Path

try:  # 包态（unittest: scripts.flowguard_lib）与脚本态（CLI: flowguard_lib）双兼容
    from ..flowguard_lib import registry
except ImportError:  # pragma: no cover
    from flowguard_lib import registry

STAGE_ZH = {
    "requirements": "需求分析", "architecture": "架构设计", "solution": "技术方案",
    "testcases": "测试用例", "hld": "概要设计", "lld": "详细设计",
    "standards": "编码规范", "review": "代码审查", "docs": "文档生成", "release": "部署交付",
}

DOC_PURPOSE = {
    "01-requirements": "需求分析阶段产出物，明确功能需求、用户故事与可验收标准；不涉及技术实现细节",
    "02-architecture": "项目级架构设计产出物，记录选型、ADR 决策与模块边界；ADR 追加式维护",
    "03-solution": "技术方案阶段产出物，明确实现选型、接口契约与风险预案",
    "04-testcases": "测试用例阶段产出物，建立 REQ 与用例、测试文件的追溯矩阵（TDD 门槛依据）",
    "05-hld": "概要设计阶段产出物，明确模块 / 服务划分、交互与非功能约束",
    "06-lld": "详细设计阶段产出物，明确事件语义、函数明细与异常边界",
    "07-standards": "项目级编码规范集，按模块栈选型；增补一律追加式并标注来源",
    "08-review": "代码审查阶段产出物，记录证据化发现项与结论（fix / wontfix / deferred）",
    "09-docs": "文档生成阶段产出物，登记功能相关文档清单与生成记录",
    "10-release": "项目级部署交付产出物，登记版本、发布内容、校验证据与回滚方案",
}

# 各产物正文（## 2. 起；full-stack-doc 章节编号约定；含占位符块不参与机械校验）
_BODY = {
    "01-requirements": """## 2. 需求范围 (Scope)

### 2.1 功能目标
> 描述本功能要解决的问题与目标

- {例如：让运维在状态文件损坏时自助恢复}

### 2.2 边界（包含 / 不包含）
| 包含 | 不包含 |
| :--- | :--- |
| {例如：由 journal 重建状态文件} | {例如：跨仓恢复、journal 修复} |

---

## 3. 用户故事与验收标准 (Requirements)

### Requirement: {{REQ_NAME}}
`__REQ_PREFIX__-1` {{SUBJECT}} SHALL {{CAPABILITY}}。

#### Scenario: {{SCENARIO_NAME}}
- **WHEN** {{前置与动作}}
- **THEN** {{可验证结果}}

> 追加 REQ 时编号递增；REQ-ID 全局唯一，格式 `<feature-id>/REQ-<n>`。

---

## 4. 验收标准汇总 (Acceptance)

- validate 零 ERROR；REQ 均被用例覆盖（见 04-testcases 追溯矩阵）。
""",

    "02-architecture": """## 2. 选型 (Technology Choices)

| 维度 | 选型 | 理由 |
| :--- | :--- | :--- |
| {例如：编排核} | {例如：Python 标准库} | {例如：零依赖分发} |

---

## 3. ADR 列表 (Architecture Decisions)

> 追加式：禁止改写既有条目；新增条目带 `feature: <来源功能>` 标注。

- ADR-{{编号}} | feature: {{来源}} | 状态: {{proposed/accepted}} —— {{决策一句话}}
  - 背景：{{...}}；备选：{{...}}；后果：{{...}}

---

## 4. 模块边界 (Module Boundaries)

| 模块 | 职责 | 依赖方向 |
| :--- | :--- | :--- |
| {{MODULE}} | {{职责}} | {{依赖}} |
""",

    "03-solution": """## 2. 实现选型 (Approach)

- {{方案要点与理由}}

---

## 3. 接口契约 (Interfaces)

```python
def {{name}}({{params}}) -> {{type}}:
    \"\"\"{{语义}}\"\"\"
```

---

## 4. 风险清单 (Risks)

| 风险 | 缓解 |
| :--- | :--- |
| {{风险}} | {{缓解措施}} |
""",

    "04-testcases": """## 2. 测试范围 (Scope)

- 覆盖：{{...}}；不覆盖：{{...}}（理由）。

---

## 3. 用例与需求追溯矩阵 (Traceability)

### 用例 TC-1: {{CASE_NAME}}
- REQ: __REQ_PREFIX__-1
- 测试文件: {{tests/test_xxx.py}}
- 步骤: {{操作序列}}
- 预期: {{可验证结果}}

> 验收机械检查：每条 REQ 至少一条用例；`测试文件` 必须已存在于仓库（执行证据最小版）。

---

## 4. 追溯说明 (Notes)

- REQ ↔ 用例 ↔ 测试文件三方对齐；覆盖率缺口在验收前清零。
""",

    "05-hld": """## 2. 模块 / 服务划分 (Components)

| 单元 | 职责 |
| :--- | :--- |
| {{单元}} | {{职责}} |

---

## 3. 交互 (Interactions)

```text
{{组件 A}} ──{{接口}}──▶ {{组件 B}}
```

---

## 4. 非功能约束 (Non-functional)

- {{性能 / 安全 / 兼容 / 失败安全等}}
""",

    "06-lld": """## 2. 明细表 (Details)

| 项目 | 字段 / 语义 | 说明 |
| :--- | :--- | :--- |
| {{项目}} | {{...}} | {{...}} |

---

## 3. 函数明细 (APIs)

```python
def {{name}}({{params}}) -> {{type}}: ...
```

---

## 4. 异常与边界 (Edge Cases)

| 情形 | 行为 |
| :--- | :--- |
| {{情形}} | {{行为}} |
""",

    "07-standards": """## 2. 规范集 (Standards)

### 2.1 {{模块 / 栈名}}
- {{规范条目；引用规范技能时给「技能名 + 安装命令」}}

---

## 3. 项目级增补记录 (Amendments)

> 追加式：禁止改写既有条目；标注来源功能。

<!-- feature: {{来源功能}} -->
- {{增补条目}}
""",

    "08-review": """## 2. 审查范围 (Scope)

- 审查对象：{{提交 / 文件范围说明}}

---

## 3. 发现项 (Findings)

### 发现: {{TITLE}}
- 证据: {{文件:行 或 提交}}
- 结论: fix|wontfix|deferred

> 验收机械检查：每条发现项都有结论。

---

## 4. 结论汇总 (Conclusion)

- {{遗留与后续}}
""",

    "09-docs": """## 2. 文档清单 (Inventory)

| 文档 | 类型 | 状态 | 链接 / 记录 |
| :--- | :--- | :--- | :--- |
| {{文档名}} | {{API/用户/运维}} | {{✅ 已实现 / 🔧 开发中 / ⏳ 计划中}} | {{...}} |

---

## 3. 生成记录 (Log)

| 日期 | 动作 | 备注 |
| :--- | :--- | :--- |
| {{DATE}} | {{...}} | {{...}} |
""",

    "10-release": """## 2. 版本信息 (Version)

| 版本号 | 发布日期 | 负责人 |
| :--- | :--- | :--- |
| {{VERSION}} | {{DATE}} | {{OWNER}} |

---

## 3. 发布内容 (Scope)

| 功能 (feature) | 状态 | 说明 |
| :--- | :--- | :--- |
| {{feature-id}} | {{✅ 已实现}} | {{...}} |

---

## 4. 校验与证据 (Evidence)

- 构建校验和（sha256）：{{...}}
- 测试证据：{{测试运行记录 / 覆盖率}}

---

## 5. 回滚方案 (Rollback)

- {{回滚步骤与验证}}
""",
}


def render(artifact_id, ctx):
    """渲染产物骨架（full-stack-doc v3.0 通用结构）。ctx: feature/title/modules/req_prefix。"""
    art = registry.ARTIFACTS[artifact_id]
    stage_zh = STAGE_ZH[art["stage"]]
    owner = f"feature: {ctx['feature']}" if art["scope"] == "feature" else "feature: project"
    req_prefix = ctx.get("req_prefix", "{{FEATURE_ID}}/REQ")
    body = _BODY[artifact_id].replace("__REQ_PREFIX__", req_prefix)
    title = ctx.get("title") or artifact_id
    return f"""<!-- 元信息 -->
<!-- artifact: {artifact_id} | {owner} | modules: {ctx.get('modules', '-')} -->
# {title} {stage_zh}文档

> **文档说明**：{DOC_PURPOSE[artifact_id]}。
>
> **版本**：V1.0.0
> **最后更新**：{{{{DATE}}}}
>
> 注：`{{{{...}}}}` 为跨文档占位符；`{{例如：...}}` 为填写提示；含占位符的块不参与机械校验。引用块 `>` 中为填写指导，填写后可删除。

---

## 1. 文档信息 (Document Info)

### 1.1 版本记录

| 版本号 | 修改日期 | 修改人 | 修改内容 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| V1.0.0 | {{{{DATE}}}} | {{{{OWNER}}}} | 初始版本 | - |

### 1.2 文档责任人

| 角色 | 姓名 | 职责 |
| :--- | :--- | :--- |
| 责任人 | {{{{OWNER}}}} | 本阶段产出、自检与送验 |

---

{body}---

**文档版本**：V1.0.0
**创建日期**：{{{{DATE}}}}
**最后更新**：{{{{DATE}}}}
**文档状态**：✅ 待评审
"""


def init_project(root):
    """建 .flowguard/ 骨架 + config.yaml 默认 + 项目级产物模板；幂等（已初始化则原样返回）。"""
    import json
    root = Path(root)
    fg = root / ".flowguard"
    for sub in ("project", "features", "journal"):
        (fg / sub).mkdir(parents=True, exist_ok=True)
    existing = fg / "project.json"
    if existing.exists():
        return json.loads(existing.read_text(encoding="utf-8"))
    try:
        from ..flowguard_lib import detect as _detect
    except ImportError:  # pragma: no cover 脚本态
        from flowguard_lib import detect as _detect
    try:
        from ..flowguard_lib import yamlmini
    except ImportError:  # pragma: no cover
        from flowguard_lib import yamlmini
    cfg_path = fg / "config.yaml"
    if not cfg_path.exists():
        cfg_path.write_text(yamlmini.dump(
            {"schema": "flowguard", "context": "", "rules": {}}), encoding="utf-8")

    det = _detect.detect(root)
    project = {
        "version": 1,
        "project": root.resolve().name,
        "stack": det["stack"],
        "modules": det["modules"],
        "current_feature": None,
        "stages": {art["stage"]: {"status": "pending", "artifact": art["rel_tpl"]}
                   for art in registry.ARTIFACTS.values() if art["scope"] == "project"},
        "features": {},
    }
    if not existing.exists():
        existing.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

    for aid in ("02-architecture", "07-standards", "10-release"):
        p = fg / registry.ARTIFACTS[aid]["rel_tpl"]
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(render(aid, {"title": project["project"], "modules": "-"}), encoding="utf-8")
    return project
