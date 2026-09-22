"""产物模板（10 份）与 init 骨架生成。模板带元信息头；内容骨架照 spec §4。"""
from pathlib import Path

from ..flowgate_lib import registry, yamlmini

STAGE_ZH = {
    "requirements": "需求分析", "architecture": "架构设计", "solution": "技术方案",
    "testcases": "测试用例", "hld": "概要设计", "lld": "详细设计",
    "standards": "编码规范", "review": "代码审查", "docs": "文档生成", "release": "部署交付",
}

_BODY = {
    "01-requirements": """\
## 用户故事与验收标准

### Requirement: <需求名>
`{req_prefix}-1` <主语> SHALL <能力>。

#### Scenario: <场景名>
- **WHEN** <前置与动作>
- **THEN** <可验证结果>

> 追加 REQ 时编号递增；REQ-ID 全局唯一，格式 `<feature-id>/REQ-<n>`。
""",
    "02-architecture": """\
## 选型
<总体技术选型>

## ADR 列表（追加式，禁止改写既有条目）
<!-- ADR-001 | feature: <来源功能或 project> | 状态: accepted -->
- ADR-001: <决策一句话> —— 背景/备选/后果

## 模块边界
<模块职责与依赖方向>
""",
    "03-solution": """\
## 实现选型
<本功能的技术方案与理由>

## 接口契约
<新增/变更的接口与数据契约>

## 风险清单
- <风险> —— <缓解>
""",
    "04-testcases": """\
## 用例与需求追溯矩阵

### 用例 TC-1: <名称>
- REQ: {req_prefix}-1
- 测试文件: tests/test_<slug>.py
- 步骤: <操作序列>
- 预期: <可验证结果>

> 验收机械检查：每条 REQ 至少一条用例；`测试文件` 必须已存在于仓库。
""",
    "05-hld": """\
## 模块/服务划分
<本功能涉及的模块与服务>

## 交互
<同步/异步交互、数据流>

## 非功能约束
<性能/安全/兼容>
""",
    "06-lld": """\
## 类/表/接口明细
<类与职责、表结构变更、接口字段明细>

## 异常与边界
<错误路径、幂等、回滚>
""",
    "07-standards": """\
## 规范集（按模块栈生成，追加式增补）
<!-- feature: <来源功能> -->
- <模块/栈>: <规范条目或引用的规范技能清单>

## 项目级增补记录
<!-- 追加式；禁止改写既有条目 -->
""",
    "08-review": """\
## 审查范围
<审查的提交/文件范围说明>

### 发现: <标题>
- 证据: <文件:行 或 提交>
- 结论: fix|wontfix|deferred

> 验收机械检查：每条发现项都有结论。
""",
    "09-docs": """\
## 文档清单
- API 文档: <生成记录或链接>
- 用户文档: <生成记录或链接>
- 运维/部署文档: <生成记录或链接>
""",
    "10-release": """\
## 版本
<版本号与日期>

## 发布内容
<本版本包含的功能（对应 feature 列表）>

## 校验与证据
- 构建校验和: <sha256>
- 测试证据: <测试运行记录/覆盖率>

## 回滚方案
<回滚步骤>
""",
}


def render(artifact_id, ctx):
    art = registry.ARTIFACTS[artifact_id]
    stage_zh = STAGE_ZH[art["stage"]]
    owner = f"feature: {ctx['feature']}" if art["scope"] == "feature" else "feature: project"
    body = _BODY[artifact_id].format(req_prefix=ctx.get("req_prefix", "<feature>/REQ"))
    title = ctx.get("title") or artifact_id
    return (
        f"<!-- 元信息 -->\n"
        f"<!-- artifact: {artifact_id} | {owner} | modules: {ctx.get('modules', '-')} -->\n"
        f"# {title} —— {stage_zh}\n\n{body}"
    )


def init_project(root):
    """建 .flowgate/ 骨架 + config.yaml 默认 + 项目级产物模板；幂等（已初始化则原样返回）。"""
    import json
    root = Path(root)
    fg = root / ".flowgate"
    for sub in ("project", "features", "journal"):
        (fg / sub).mkdir(parents=True, exist_ok=True)
    existing = fg / "project.json"
    if existing.exists():
        return json.loads(existing.read_text(encoding="utf-8"))
    cfg_path = fg / "config.yaml"
    if not cfg_path.exists():
        cfg_path.write_text(yamlmini.dump(
            {"schema": "flowgate", "context": "", "rules": {}}), encoding="utf-8")

    from ..flowgate_lib import detect as _detect
    det = _detect.detect(root)
    project = {
        "version": 1,
        "project": root.resolve().name,
        "stack": det["stack"],
        "modules": det["modules"],
        "current_feature": None,
        "stages": {aid: {"status": "pending", "artifact": art["rel_tpl"]}
                   for aid, art in registry.ARTIFACTS.items() if art["scope"] == "project"},
        "features": {},
    }
    _atomic_write_json(fg / "project.json", project)

    for aid in ("02-architecture", "07-standards", "10-release"):
        p = fg / registry.ARTIFACTS[aid]["rel_tpl"]
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(render(aid, {"title": project["project"], "modules": "-"}), encoding="utf-8")
    return project


def _atomic_write_json(path, data):
    import json
    if not path.exists():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
