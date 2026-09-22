"""会话 + worktree + 任务上下文存储。

这里只保存治理元数据；正式规格正文始终留在原生 SDD 目录。
"""
import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path

from . import discovery, state

TASK_TYPES = ("read_only", "simple_change", "important_change", "incident")
SPEC_SYSTEMS = ("none", "spec-kit", "openspec", "superpowers", "external")


class ContextError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _dir(root, *, create=False):
    path = Path(root) / ".flowguard" / "contexts"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _read_json(path, label):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContextError(f"{label} 损坏或不可读: {path}") from error


def _index(root):
    path = _dir(root) / "index.json"
    if not path.exists():
        return {"version": 1, "active": {}}
    return _read_json(path, "上下文索引")


def _key(session_id, worktree_id):
    return f"{session_id}:{worktree_id}"


def load(root, context_id):
    if not context_id:
        raise ContextError("上下文 id 不能为空")
    path = _dir(root) / f"{context_id}.json"
    if not path.exists():
        raise ContextError(f"上下文不存在: {context_id}")
    return _read_json(path, "上下文")


def save(root, data):
    data["updated_at"] = _now()
    _atomic_write(_dir(root, create=True) / f"{data['context_id']}.json", data)
    return data


def list_all(root):
    directory = _dir(root)
    if not directory.exists():
        return []
    return [
        _read_json(path, "上下文")
        for path in sorted(directory.glob("*.json"))
        if path.name != "index.json"
    ]


def _validate_spec_ref(root, spec_system, spec_ref):
    if spec_system not in SPEC_SYSTEMS:
        raise ContextError(f"未知规格体系: {spec_system}")
    if not spec_ref:
        return None
    if spec_ref.startswith(("http://", "https://")):
        if spec_system != "external":
            raise ContextError("外部 URL 必须使用 spec_system=external")
        return spec_ref
    target = (Path(root) / spec_ref).resolve()
    root_path = Path(root).resolve()
    if root_path not in target.parents and target != root_path:
        raise ContextError("spec_ref 必须位于目标仓库内，外部引用请使用 URL")
    if not target.exists():
        raise ContextError(f"规格引用不存在: {spec_ref}")
    return str(target.relative_to(root_path)).replace("\\", "/")


def _assert_acyclic(root, candidate):
    items = {item["context_id"]: item for item in list_all(root)}
    items[candidate["context_id"]] = candidate
    visiting = []
    visited = set()

    def visit(context_id):
        if context_id in visiting:
            cycle = visiting[visiting.index(context_id):] + [context_id]
            raise ContextError("任务依赖成环: " + " -> ".join(cycle))
        if context_id in visited:
            return
        visiting.append(context_id)
        item = items[context_id]
        edges = list(item.get("depends_on") or [])
        if item.get("parent_id"):
            edges.append(item["parent_id"])
        for dependency in edges:
            if dependency in items:
                visit(dependency)
        visiting.pop()
        visited.add(context_id)

    for context_id in items:
        visit(context_id)


def bind(root, *, session_id, task_id, task_type, spec_system, spec_ref,
         parent_id=None, depends_on=None, required_evidence=None):
    with state.state_lock(root):
        return _bind_unlocked(
            root, session_id=session_id, task_id=task_id, task_type=task_type,
            spec_system=spec_system, spec_ref=spec_ref, parent_id=parent_id,
            depends_on=depends_on, required_evidence=required_evidence,
        )


def _bind_unlocked(root, *, session_id, task_id, task_type, spec_system, spec_ref,
                   parent_id=None, depends_on=None, required_evidence=None):
    if not session_id or not task_id:
        raise ContextError("session_id 和 task_id 必填")
    if task_type not in TASK_TYPES:
        raise ContextError(f"未知任务类型: {task_type}")
    spec_ref = _validate_spec_ref(root, spec_system, spec_ref)
    snapshot = discovery.discover(root)
    worktree_id = snapshot["git"]["worktree_id"]
    seed = f"{session_id}|{worktree_id}|{task_id}"
    context_id = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    if parent_id:
        load(root, parent_id)
    for dependency in depends_on or []:
        load(root, dependency)

    now = _now()
    existing = None
    try:
        existing = load(root, context_id)
    except ContextError:
        pass
    new_core = {
        "task_type": task_type,
        "spec_system": spec_system,
        "spec_ref": spec_ref,
        "parent_id": parent_id,
        "depends_on": list(depends_on or []),
    }
    unchanged_scope = bool(existing) and all(existing.get(key) == value for key, value in new_core.items())
    data = {
        "version": 1,
        "context_id": context_id,
        "session_id": session_id,
        "worktree_id": worktree_id,
        "task_id": task_id,
        "task_type": task_type,
        "spec_system": spec_system,
        "spec_ref": spec_ref,
        "status": "active",
        "parent_id": parent_id,
        "depends_on": new_core["depends_on"],
        "required_evidence": list(required_evidence or []),
        "approvals": existing.get("approvals", {}) if unchanged_scope else {},
        "created_at": existing.get("created_at", now) if existing else now,
        "updated_at": now,
    }
    _assert_acyclic(root, data)

    index = _index(root)
    active_key = _key(session_id, worktree_id)
    previous_id = index["active"].get(active_key)
    if previous_id and previous_id != context_id:
        previous = load(root, previous_id)
        if previous.get("status") == "active":
            previous["status"] = "paused"
            save(root, previous)
    save(root, data)
    index["active"][active_key] = context_id
    _atomic_write(_dir(root, create=True) / "index.json", index)
    return data


def active(root, session_id):
    snapshot = discovery.discover(root)
    index = _index(root)
    context_id = index["active"].get(_key(session_id, snapshot["git"]["worktree_id"]))
    return load(root, context_id) if context_id else None


def approve(root, context_id, approval, *, actor):
    with state.state_lock(root):
        return _approve_unlocked(root, context_id, approval, actor=actor)


def _approve_unlocked(root, context_id, approval, *, actor):
    if not actor:
        raise ContextError("批准必须记录 actor")
    data = load(root, context_id)
    data.setdefault("approvals", {})[approval] = {"actor": actor, "at": _now()}
    return save(root, data)


def blockers(root, context_id):
    data = load(root, context_id)
    missing = []
    for dependency in data.get("depends_on", []):
        if load(root, dependency).get("status") != "completed":
            missing.append(f"dependency:{dependency}")
    for child in list_all(root):
        if child.get("parent_id") == context_id and child.get("status") not in ("completed", "dropped"):
            missing.append(f"child:{child['context_id']}")
    return missing


def complete(root, context_id):
    with state.state_lock(root):
        return _complete_unlocked(root, context_id)


def _complete_unlocked(root, context_id):
    missing = blockers(root, context_id)
    if missing:
        if any(item.startswith("child:") for item in missing):
            raise ContextError("仍有未完成的必要子任务: " + ", ".join(missing))
        raise ContextError("仍有未完成依赖: " + ", ".join(missing))
    data = load(root, context_id)
    data["status"] = "completed"
    return save(root, data)
