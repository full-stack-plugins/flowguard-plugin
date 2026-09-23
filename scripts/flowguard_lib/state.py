"""三级结构状态机：project.json + features/<id>/state.json，合法迁移表单源。"""
import contextlib
import datetime
import fcntl
import json
import os
import pathlib
import stat
import tempfile

STAGE_STATUSES = ("pending", "in_progress", "pending_acceptance", "accepted", "skipped", "overridden")
FEATURE_STATUSES = ("active", "done", "dropped")

# 合法迁移（唯一事实源；测试做全矩阵断言）
LEGAL = {
    "pending": ("in_progress",),
    "in_progress": ("pending_acceptance",),
    "pending_acceptance": ("accepted", "skipped", "in_progress"),
    "accepted": ("in_progress",),
    "skipped": ("in_progress",),
    "overridden": ("in_progress",),
}

# 下游依赖：某阶段产物回改时须一并降级的阶段（spec §4.4 降级瀑布）
DOWNSTREAM = {
    "requirements": ("testcases", "review", "docs"),
    "solution": ("testcases", "review", "docs"),
    "testcases": ("review", "docs"),
    "hld": ("lld", "review", "docs"),
    "lld": ("review", "docs"),
    "review": ("docs",),
    "architecture": ("requirements", "solution", "testcases", "hld", "lld", "review", "docs"),
    "standards": ("review", "docs"),
}


class StateError(Exception):
    pass


@contextlib.contextmanager
def state_lock(root):
    """fcntl 独占锁（LOCK_NB），锁冲突快速失败。"""
    from .runtime import repository_state_dir
    lock = repository_state_dir(root, create=True) / ".lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    fh = lock.open("w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise StateError("状态文件被其它进程锁定，请稍后重试")
    try:
        yield
    finally:
        fh.close()


def _flowguard_dir(root, *, create=False):
    d = pathlib.Path(root) / ".flowguard"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def atomic_write_text(path, content):
    """同目录临时文件替换文档；写入或替换失败时保留旧正文。"""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    fd, temporary = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        pathlib.Path(temporary).unlink(missing_ok=True)


def atomic_create_text(path, content, *, mode=None):
    """原子创建新文档，不覆盖并发创建的目标，也不留下半写文件。"""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".flowguard-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.link(temporary, path)
    finally:
        pathlib.Path(temporary).unlink(missing_ok=True)


def load_project(root):
    p = _flowguard_dir(root) / "project.json"
    if not p.exists():
        raise StateError("缺少 .flowguard/project.json，请先运行 /flowguard-init")
    return json.loads(p.read_text(encoding="utf-8"))


def save_project(root, data):
    _atomic_write(_flowguard_dir(root, create=True) / "project.json", data)


def _feature_path(root, feature_id, *, create=False):
    return _flowguard_dir(root, create=create) / "features" / feature_id / "state.json"


def load_feature(root, feature_id):
    p = _feature_path(root, feature_id)
    if not p.exists():
        raise StateError(f"功能不存在: {feature_id}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_feature(root, data):
    _atomic_write(_feature_path(root, data["feature"], create=True), data)


def transition_stage(owner, stage, target, *, reason="", evidence=None):
    """单一状态迁移入口；非法迁移/缺失理由抛 StateError。"""
    cur = owner["stages"][stage]["status"]
    if target not in LEGAL.get(cur, ()):
        raise StateError(f"非法状态迁移 {cur} → {target}（合法目标: {LEGAL.get(cur, ())}）")
    if target in ("skipped", "overridden") and not reason:
        raise StateError(f"{target} 必须填写理由")
    owner["stages"][stage]["status"] = target
    if reason:
        owner["stages"][stage]["reason"] = reason
    if target == "accepted":
        owner["stages"][stage]["accepted_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if evidence:
        owner["stages"][stage]["evidence"] = evidence


def transition_override(owner, stage, *, reason):
    """override 逃生口：任意态 → overridden（spec §4.4），必须用户发起 + 理由。"""
    if not reason:
        raise StateError("override 必须填写理由")
    owner["stages"][stage]["status"] = "overridden"
    owner["stages"][stage]["reason"] = reason


def degrade_from(owner, stage):
    """stage 及其下游中已 accepted/pending_acceptance 的阶段降回 in_progress，返回被降级列表。"""
    chain = [stage] + [s for s in DOWNSTREAM.get(stage, ()) if s in owner["stages"]]
    hit = []
    for s in chain:
        if owner["stages"][s]["status"] in ("accepted", "pending_acceptance"):
            owner["stages"][s]["status"] = "in_progress"
            hit.append(s)
    return hit
