"""门禁判定链入口：路径分类 + 动作解锁（spec §5）。

原则：未初始化的 .flowgate 一律放行（防误伤）；门禁拒绝时产出诊断信封。
"""
from . import registry, state


def _classify(project, path):
    if not path:
        return "other"
    p = str(path).replace("\\", "/")
    if p.startswith(".flowgate/") or p == ".flowgate":
        return "artifact"
    m = registry.match_module(project, p)
    return f"module:{m}" if m else "other"


def classify_path(root, path):
    try:
        project = state.load_project(root)
    except state.StateError:
        return "other"
    return _classify(project, path)


def check_action(root, action, *, path=None, feature=None):
    """返回 {"allowed": bool, "envelope": dict|None}；任何状态读取异常都放行（防误伤）。"""
    try:
        project = state.load_project(root)
        fid = feature or project.get("current_feature")
        fstate = state.load_feature(root, fid) if fid else None
    except state.StateError:
        return {"allowed": True, "envelope": None}
    allowed, env = registry.unlock_check(action, project, fstate, path=path)
    return {"allowed": allowed, "envelope": env}
