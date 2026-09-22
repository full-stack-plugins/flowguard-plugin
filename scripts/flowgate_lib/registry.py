"""阶段/artifact DAG 注册表 + 动作解锁表（十阶段，spec v3.1 §2.1/§3.1/§5.1）。

跨 scope requires 语义（台账裁定）：项目级 artifact 依赖功能级 artifact 时，
「所有 active 功能的对应 artifact 均 done|skipped|overridden」即满足；无 active 功能时空满足。
"""
from pathlib import Path

from .diag import envelope
from .state import StateError  # noqa: F401  (re-export 供测试/调用方)

ARTIFACTS = {
    "01-requirements": {"scope": "feature", "stage": "requirements",
                        "rel_tpl": "features/{feature}/artifacts/01-requirements.md",
                        "requires": ()},
    "02-architecture": {"scope": "project", "stage": "architecture",
                        "rel_tpl": "project/02-architecture.md",
                        "requires": ()},
    "03-solution": {"scope": "feature", "stage": "solution",
                    "rel_tpl": "features/{feature}/artifacts/03-solution.md",
                    "requires": ("01-requirements", "02-architecture")},
    "04-testcases": {"scope": "feature", "stage": "testcases",
                     "rel_tpl": "features/{feature}/artifacts/04-testcases.md",
                     "requires": ("03-solution",)},
    "05-hld": {"scope": "feature", "stage": "hld",
               "rel_tpl": "features/{feature}/artifacts/05-hld.md",
               "requires": ("04-testcases",)},
    "06-lld": {"scope": "feature", "stage": "lld",
               "rel_tpl": "features/{feature}/artifacts/06-lld.md",
               "requires": ("05-hld",)},
    "07-standards": {"scope": "project", "stage": "standards",
                     "rel_tpl": "project/07-standards.md",
                     "requires": ()},
    "08-review": {"scope": "feature", "stage": "review",
                  "rel_tpl": "features/{feature}/artifacts/08-review.md",
                  "requires": ("06-lld", "07-standards")},
    "09-docs": {"scope": "feature", "stage": "docs",
                "rel_tpl": "features/{feature}/artifacts/09-docs.md",
                "requires": ("08-review",)},
    "10-release": {"scope": "project", "stage": "release",
                   "rel_tpl": "project/10-release.md",
                   "requires": ("07-standards", "09-docs")},
}

STAGE_ORDER = ("requirements", "architecture", "solution", "testcases", "hld", "lld",
               "standards", "review", "docs", "release")

# Tier 2 执行技能引用（spec §7：上游 5 仓 0 tag，九个 Tier 1 全部降 Tier 2；含长尾按栈技能）
TIER2_REFS = {
    "requirements": [("feature-design", "design-skills"), ("ddd-domain-designer", "ddd-skills")],
    "solution": [("ddd-domain-designer", "ddd-skills"), ("ddd-architecture-doc", "ddd-skills")],
    "testcases": [("ddd-testing-strategist", "ddd-skills"), ("python-testing-patterns", "python-skills"),
                  ("junit-mockito-patterns", "java-skills")],
    "standards": [("java-development-manual", "java-skills"), ("java-conventions", "java-skills"),
                  ("python-code-style", "python-skills"), ("rust-style-clippy", "rust-skills")],
    "architecture": [("ddd-architecture-selector", "ddd-skills")],
    "review": [("ddd-code-reviewer", "ddd-skills"), ("kotlin-code-review", "kotlin-skills"),
               ("rust-code-review", "rust-skills"), ("swift-code-review", "swift-skills"),
               ("zig-code-review", "zig-skills")],
    "docs": [("full-stack-doc", "document-skills"), ("api-doc-generator", "document-skills")],
    "release": [("easy4j-deploy", "java-skills"), ("fw-release-gate", "firmware-skills")],
}

OK_STATUSES = ("accepted", "skipped", "overridden")

# 构建/发布类 Bash 命令模式（gate 钩子用于把 Bash 归类为 build_release 动作）
RELEASE_CMD_PATTERNS = (
    "mvn deploy", "mvn release", "gradle publish", "gradle release",
    "npm publish", "yarn publish", "pnpm publish", "cargo publish",
    "docker push", "helm push", "twine upload", "make release",
)


def install_cmd(skill, pkg):
    return f"npx skills add full-stack-skills/{pkg} --skill {skill}"


def _check_acyclic_graph(graph):
    """graph: {id: {"requires": (...)}}；DFS 环检测，含环路径报错。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in graph}
    stack_path = []

    def visit(nid):
        color[nid] = GRAY
        stack_path.append(nid)
        for dep in graph[nid].get("requires", ()):
            if dep not in graph:
                raise StateError(f"requires 引用不存在的 artifact: {dep}")
            if color[dep] == GRAY:
                cycle = stack_path[stack_path.index(dep):] + [dep]
                raise StateError("artifact 依赖成环: " + " -> ".join(cycle))
            if color[dep] == WHITE:
                visit(dep)
        stack_path.pop()
        color[nid] = BLACK

    for nid in graph:
        if color[nid] == WHITE:
            visit(nid)


def check_acyclic():
    _check_acyclic_graph(ARTIFACTS)


def topo_order():
    """Kahn 拓扑 + 声明顺序破平局（刻意不用字母序，照 OpenSpec artifact-graph）。"""
    check_acyclic()
    indeg = {nid: 0 for nid in ARTIFACTS}
    dependents = {nid: [] for nid in ARTIFACTS}
    for nid, art in ARTIFACTS.items():
        for dep in art["requires"]:
            indeg[nid] += 1
            dependents[dep].append(nid)
    ready = [nid for nid in ARTIFACTS if indeg[nid] == 0]
    out = []
    while ready:
        nid = ready.pop(0)  # 声明序（dict 序）即优先序
        out.append(nid)
        for d in dependents[nid]:
            indeg[d] -= 1
            if indeg[d] == 0:
                ready.append(d)
    return out


def _owner_stages(aid, project, feature):
    art = ARTIFACTS[aid]
    if art["scope"] == "project":
        return project["stages"]
    return feature["stages"] if feature else {}


def _artifact_file(aid, project, feature, root):
    art = ARTIFACTS[aid]
    rel = art["rel_tpl"].format(feature=(feature or {}).get("feature", "_"))
    return Path(root) / ".flowgate" / rel


def artifact_status(aid, project, feature, root=None):
    """DAG 派生子状态：done|skipped|ready|blocked（+ missing deps）。"""
    art = ARTIFACTS[aid]
    st = _owner_stages(aid, project, feature).get(art["stage"], {}).get("status", "pending")
    if st in ("skipped", "overridden"):
        return "skipped", []
    if root is not None and _artifact_file(aid, project, feature, root).exists():
        return "done", []
    missing = []
    for dep in art["requires"]:
        if not _dep_ok(dep, project, feature, root):
            missing.append(dep)
    return ("ready", []) if not missing else ("blocked", missing)


def _dep_ok(dep, project, feature, root):
    dep_art = ARTIFACTS[dep]
    if dep_art["scope"] == "project" or feature is not None:
        stages = _owner_stages(dep, project, feature)
        if stages.get(dep_art["stage"], {}).get("status") in OK_STATUSES:
            return True
        st, _ = artifact_status(dep, project, feature, root)
        return st in ("done", "skipped")
    # 项目级 artifact 依赖功能级 artifact：所有 active 功能均满足才放行（台账裁定）
    active = {fid: f for fid, f in project.get("features", {}).items() if f.get("status") == "active"}
    if not active:
        return True
    for fid in active:
        f = {"feature": fid, "stages": _load_active_feature_stages(project, fid)}
        st, _ = artifact_status(dep, project, f, root)
        if st not in ("done", "skipped"):
            return False
    return True


def _load_active_feature_stages(project, fid):
    """活动功能的阶段状态直接取索引；完整 state.json 由调用方持有（此处尽力而为）。"""
    # project.json 不冗余存 stages；若需精确状态，调用方应传 feature。此处按文件存在性判定由
    # artifact_status(root) 完成；无 root 时保守视为未满足。
    return {}


def match_module(project, path):
    """路径 → 模块名；不在任何 src_roots 返回 None。src_roots 为 "." 表示整仓。"""
    if not path:
        return None
    p = str(path).replace("\\", "/")
    for name, mod in (project.get("modules") or {}).items():
        for sr in mod.get("src_roots", []):
            if sr == ".":
                return name
            if p == sr or p.startswith(sr.rstrip("/") + "/"):
                return name
    return None


def unlock_check(action, project, feature, path=None):
    """动作解锁表（spec §5.1）。返回 (allowed, envelope|None)。"""
    if action == "write_code":
        m = match_module(project, path)
        if m is None:
            return True, None
        if not feature or feature.get("status") != "active":
            return False, envelope("ERROR", "gate_write_code_no_module",
                                   f"路径属于模块 {m}，但当前无 active 功能上下文",
                                   "用 /flowgate-next --feature X 进入功能，或 /flowgate-feature new 声明涉及模块")
        if m not in (feature.get("modules") or []):
            return False, envelope("ERROR", "gate_write_code_feature_mismatch",
                                   f"模块 {m} 不属于当前功能 {feature.get('feature')}",
                                   f"在功能 {feature.get('feature')} 中补声明模块 {m}，或切换 current_feature")
        notok = [s for s in ("requirements", "solution", "testcases", "hld", "lld")
                 if feature["stages"].get(s, {}).get("status") not in OK_STATUSES]
        if notok:
            return False, envelope("ERROR", "gate_write_code_tdd",
                                   f"写码前置阶段未验收: {', '.join(notok)}",
                                   f"先完成并验收 {notok[0]}（/flowgate-advance --feature {feature.get('feature')}）")
        std = project["stages"].get("standards", {}).get("status", "pending")
        if std == "pending":
            return False, envelope("ERROR", "gate_write_code_no_standards",
                                   "项目编码规范（07-standards）尚未生成",
                                   "先推进 standards 阶段生成规范集")
        return True, None

    if action == "write_review":
        notok = [s for s in ("testcases", "hld", "lld")
                 if feature["stages"].get(s, {}).get("status") not in OK_STATUSES]
        if notok:
            return False, envelope("ERROR", "gate_review_needs_testcases",
                                   f"审查前置阶段未验收: {', '.join(notok)}",
                                   f"先验收 {notok[0]}")
        if project["stages"].get("standards", {}).get("status") not in OK_STATUSES:
            return False, envelope("ERROR", "gate_review_needs_standards",
                                   "项目编码规范未验收，审查缺少规范依据",
                                   "先验收 07-standards")
        return True, None

    if action == "write_docs":
        if feature["stages"].get("review", {}).get("status") not in OK_STATUSES:
            return False, envelope("ERROR", "gate_docs_needs_review",
                                   "代码审查未验收，文档阶段未解锁",
                                   "先完成并验收 08-review")
        return True, None

    if action == "build_release":
        if project["stages"].get("standards", {}).get("status") not in OK_STATUSES:
            return False, envelope("ERROR", "gate_review_needs_standards",
                                   "项目编码规范未验收，不可发布",
                                   "先验收 07-standards")
        active = [fid for fid, f in (project.get("features") or {}).items() if f.get("status") == "active"]
        if active:
            return False, envelope("ERROR", "gate_release_active_features",
                                   f"仍有 active 功能: {', '.join(active)}",
                                   "将各功能 done（/flowgate-advance）或 drop（留痕）后交付")
        return True, None

    raise ValueError(f"未知动作: {action}")
