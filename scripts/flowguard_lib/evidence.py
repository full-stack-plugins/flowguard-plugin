"""带代码指纹的治理证据仓。"""
import datetime
import hashlib
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from . import context as context_store, state

KINDS = (
    "spec_verified", "tests", "static_analysis", "semantic_review",
    "user_acceptance", "release_readiness",
)
RESULTS = ("pass", "fail", "warning")


class EvidenceError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _git(root, *args, text=False):
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=text, check=False,
    )


def code_fingerprint(root):
    """计算 HEAD + 工作树内容指纹；排除 FlowGuard 自身治理元数据。"""
    root = Path(root).resolve()
    digest = hashlib.sha256()
    head = _git(root, "rev-parse", "HEAD", text=True)
    if head.returncode == 0:
        digest.update(head.stdout.strip().encode("utf-8"))
        diff = _git(root, "diff", "--binary", "HEAD", "--", ".", ":(exclude).flowguard")
        digest.update(diff.stdout)
        others = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
        for raw in sorted(item for item in others.stdout.split(b"\0") if item):
            rel = raw.decode("utf-8", errors="surrogateescape")
            if rel == ".flowguard" or rel.startswith(".flowguard/"):
                continue
            digest.update(raw)
            path = root / rel
            if path.is_file():
                digest.update(path.read_bytes())
    else:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or ".flowguard" in path.parts or ".git" in path.parts:
                continue
            digest.update(str(path.relative_to(root)).encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _dir(root, context_id, *, create=False):
    path = Path(root) / ".flowguard" / "evidence" / context_id
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _write(path, value):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def record(root, context_id, *, kind, producer, result, summary, source_ref,
           expires_on_change=None):
    with state.state_lock(root):
        return _record_unlocked(
            root, context_id, kind=kind, producer=producer, result=result,
            summary=summary, source_ref=source_ref, expires_on_change=expires_on_change,
        )


def _record_unlocked(root, context_id, *, kind, producer, result, summary, source_ref,
                     expires_on_change=None):
    try:
        context_store.load(root, context_id)
    except context_store.ContextError as error:
        raise EvidenceError(str(error)) from error
    if kind not in KINDS:
        raise EvidenceError(f"未知证据类型: {kind}")
    if result not in RESULTS:
        raise EvidenceError(f"未知证据结果: {result}")
    if not producer or not summary or not source_ref:
        raise EvidenceError("producer、summary、source_ref 必填")
    evidence_id = f"{kind}-{uuid.uuid4().hex[:12]}"
    if expires_on_change is None:
        expires_on_change = kind != "user_acceptance"
    data = {
        "version": 1,
        "evidence_id": evidence_id,
        "context_id": context_id,
        "kind": kind,
        "producer": producer,
        "result": result,
        "summary": summary,
        "source_ref": source_ref,
        "code_fingerprint": code_fingerprint(root),
        "created_at": _now(),
        "expires_on_change": bool(expires_on_change),
        "status": "active",
    }
    _write(_dir(root, context_id, create=True) / f"{evidence_id}.json", data)
    for previous in list_all(root, context_id):
        if (
            previous["evidence_id"] != evidence_id
            and previous.get("kind") == kind
            and previous.get("status") == "active"
        ):
            previous["status"] = "superseded"
            previous["superseded_at"] = data["created_at"]
            previous["superseded_by"] = evidence_id
            _write(
                _dir(root, context_id, create=True) / f"{previous['evidence_id']}.json",
                previous,
            )
    return data


def load(root, context_id, evidence_id):
    path = _dir(root, context_id) / f"{evidence_id}.json"
    if not path.exists():
        raise EvidenceError(f"证据不存在: {evidence_id}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceError(f"证据损坏或不可读: {evidence_id}") from error


def list_all(root, context_id):
    directory = _dir(root, context_id)
    if not directory.exists():
        return []
    return [load(root, context_id, path.stem) for path in sorted(directory.glob("*.json"))]


def refresh_staleness(root, context_id):
    with state.state_lock(root):
        return _refresh_staleness_unlocked(root, context_id)


def _refresh_staleness_unlocked(root, context_id):
    current = code_fingerprint(root)
    stale = []
    for item in list_all(root, context_id):
        if (
            item.get("status") == "active"
            and item.get("expires_on_change")
            and item.get("code_fingerprint") != current
        ):
            item["status"] = "stale"
            item["stale_at"] = _now()
            _write(_dir(root, context_id, create=True) / f"{item['evidence_id']}.json", item)
            stale.append(item["evidence_id"])
    return stale


def valid_kinds(root, context_id):
    refresh_staleness(root, context_id)
    latest = {}
    for item in list_all(root, context_id):
        if item.get("status") != "active":
            continue
        previous = latest.get(item["kind"])
        if previous is None or item.get("created_at", "") > previous.get("created_at", ""):
            latest[item["kind"]] = item
    return {kind for kind, item in latest.items() if item.get("result") == "pass"}
