"""阶段/artifact DAG 注册表（十阶段，spec v3.1 §2.1/§3.1）。

requires 语义：项目级 artifact 依赖功能级 artifact 时，前置满足以 docs/
阶段文档状态为准（stage_docs 按声明序检查全部前置）。
"""
from .state import StateError  # noqa: F401  (re-export 供测试/调用方)

ARTIFACTS = {
    "01-requirements": {"scope": "feature", "stage": "requirements",
                        "requires": ()},
    "02-architecture": {"scope": "project", "stage": "architecture",
                        "requires": ()},
    "03-solution": {"scope": "feature", "stage": "solution",
                    "requires": ("01-requirements", "02-architecture")},
    "04-testcases": {"scope": "feature", "stage": "testcases",
                     "requires": ("03-solution",)},
    "05-hld": {"scope": "feature", "stage": "hld",
               "requires": ("04-testcases",)},
    "06-lld": {"scope": "feature", "stage": "lld",
               "requires": ("05-hld",)},
    "07-standards": {"scope": "project", "stage": "standards",
                     "requires": ()},
    "08-review": {"scope": "feature", "stage": "review",
                  "requires": ("06-lld", "07-standards")},
    "09-docs": {"scope": "feature", "stage": "docs",
                "requires": ("08-review",)},
    "10-release": {"scope": "project", "stage": "release",
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

# 发布命令的兼容文本模式；直接 CLI 的带选项调用由 Hook 词法分类补充。
RELEASE_CMD_PATTERNS = (
    "mvn deploy", "mvn release", "gradle publish", "gradle release",
    "npm publish", "yarn publish", "pnpm publish", "cargo publish",
    "docker push", "helm push", "twine upload", "make release",
    "gh release create", "gh release upload",
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
