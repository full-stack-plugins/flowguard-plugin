"""把可追溯检查结果登记在十阶段文档内。"""
import datetime
import hashlib
import os
import re
import subprocess
import uuid
from pathlib import Path

from . import context as context_store, stage_docs, state

KINDS = ("spec_verified", "tests", "static_analysis", "semantic_review", "user_acceptance", "release_readiness")
RESULTS = ("pass", "fail", "warning")
SPEC_DOC_STAGES = (
    "01-requirements", "02-architecture", "03-solution", "04-testcases",
    "05-hld", "06-lld", "07-standards",
)
NATIVE_SPEC_DIRS = (".specify/", "openspec/", "docs/superpowers/")
STAGE_FOR_KIND = {
    "spec_verified": "01-requirements", "tests": "04-testcases",
    "static_analysis": "08-review", "semantic_review": "08-review",
    "user_acceptance": "10-release", "release_readiness": "10-release",
}
START = "<!-- FLOWGUARD_EVIDENCE_START -->"
END = "<!-- FLOWGUARD_EVIDENCE_END -->"
HEADER = (
    "## 11. FlowGuard 检查证据\n\n"
    "| ID | 上下文 | 类型 | 生产者 | 结果 | 摘要 | 来源引用 | 代码指纹 | 时间 | 随代码过期 | 状态 |\n"
    "|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|\n"
)
OLD_HEADER = (
    "## 11. FlowGuard 检查证据\n\n"
    "| ID | 类型 | 生产者 | 结果 | 摘要 | 来源引用 | 代码指纹 | 时间 | 随代码过期 | 状态 |\n"
    "|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|\n"
)


class EvidenceError(Exception):
    pass


class GitStateError(EvidenceError):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _git(root, *args, text=False):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=text, check=False)
    except OSError as error:
        raise GitStateError("无法读取 Git 状态") from error


def _hash_bound_spec(digest, root, spec_ref):
    if not spec_ref or spec_ref.startswith(("http://", "https://")):
        return
    target = (root / spec_ref).resolve()
    if target != root and root not in target.parents:
        digest.update(b"<spec-ref-outside-repository>")
        return
    if target.is_file():
        paths = [target]
    elif target.is_dir():
        paths = sorted(path for path in target.rglob("*") if path.is_file())
    else:
        digest.update(b"<missing-bound-spec>")
        return
    for path in paths:
        if path.is_symlink() or root not in path.resolve().parents:
            digest.update(f"<unsafe-spec-path:{path.relative_to(root)}>".encode("utf-8"))
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())


def code_fingerprint(root, ctx):
    """对代码、正式规格与当前任务及父级的前置阶段正文取指纹。"""
    root = Path(root).resolve()
    digest = hashlib.sha256()
    head = _git(root, "rev-parse", "HEAD", text=True)
    if head.returncode == 0:
        digest.update(head.stdout.strip().encode("utf-8"))
        diff = _git(root, "diff", "--binary", "HEAD", "--", ".",
                    ":(exclude)docs/features", ":(exclude)docs/project",
                    ":(exclude)docs/legacy-flowguard", ":(exclude).flowguard",
                    ":(exclude).specify", ":(exclude)openspec",
                    ":(exclude)docs/superpowers")
        if diff.returncode:
            raise GitStateError("无法读取 Git 工作树差异")
        digest.update(diff.stdout)
        others = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
        if others.returncode:
            raise GitStateError("无法读取 Git 未跟踪文件")
        for raw in sorted(item for item in others.stdout.split(b"\0") if item):
            rel = raw.decode("utf-8", errors="surrogateescape")
            if rel.startswith(("docs/features/", "docs/project/", "docs/legacy-flowguard/", ".flowguard/", *NATIVE_SPEC_DIRS)):
                continue
            digest.update(raw)
            path = root / rel
            if path.is_symlink():
                digest.update(os.fsencode(os.readlink(path)))
            elif path.is_file():
                digest.update(path.read_bytes())
    else:
        files = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        if files.returncode:
            raise GitStateError("无法读取初始 Git 工作树文件")
        for raw in sorted(set(item for item in files.stdout.split(b"\0") if item)):
            rel = raw.decode("utf-8", errors="surrogateescape")
            if rel.startswith(("docs/features/", "docs/project/", "docs/legacy-flowguard/", ".flowguard/", *NATIVE_SPEC_DIRS)):
                continue
            digest.update(raw)
            path = root / rel
            if path.is_symlink():
                digest.update(os.fsencode(os.readlink(path)))
            elif path.is_file():
                digest.update(path.read_bytes())
            else:
                digest.update(b"<missing>")
    current_ctx = ctx
    seen_contexts = set()
    while current_ctx:
        context_id = current_ctx["context_id"]
        if context_id in seen_contexts:
            digest.update(b"<cyclic-parent>")
            break
        seen_contexts.add(context_id)
        task_id = current_ctx["task_id"]
        digest.update(f"task:{task_id}".encode("utf-8"))
        for key in ("spec_system", "spec_ref"):
            digest.update(f"{key}\0{current_ctx.get(key) or ''}\0".encode("utf-8"))
        _hash_bound_spec(digest, root, current_ctx.get("spec_ref"))
        for stage in SPEC_DOC_STAGES:
            path = stage_docs.path_for(root, task_id, stage)
            digest.update(stage.encode("utf-8"))
            digest.update(
                stage_docs._content_hash(path.read_text(encoding="utf-8")).encode("utf-8")
                if path.is_file() else b"<missing>"
            )
        parent_id = current_ctx.get("parent_id")
        if not parent_id:
            break
        try:
            current_ctx = context_store.load(root, parent_id)
        except context_store.ContextError:
            digest.update(f"<missing-parent:{parent_id}>".encode("utf-8"))
            break
    return digest.hexdigest()


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _evidence_path(root, task_id, kind):
    return stage_docs.path_for(root, task_id, STAGE_FOR_KIND[kind])


def _append(path, item):
    content = path.read_text(encoding="utf-8")
    row = "| " + " | ".join(_cell(item[key]) for key in (
        "evidence_id", "context_id", "kind", "producer", "result", "summary", "source_ref",
        "code_fingerprint", "created_at", "expires_on_change", "status",
    )) + " |\n"
    if START in content and END in content:
        content = content.replace(OLD_HEADER, HEADER, 1)
        content = content.replace(END, row + END, 1)
    else:
        footer = "\n---\n\n**文档版本**"
        section = f"\n{START}\n{HEADER}{row}{END}\n"
        content = content.replace(footer, section + footer, 1) if footer in content else content + section
    state.atomic_write_text(path, content)


def record(root, context_id, *, kind, producer, result, summary, source_ref,
           expires_on_change=None):
    with state.state_lock(root):
        return _record_unlocked(root, context_id, kind=kind, producer=producer,
                                result=result, summary=summary, source_ref=source_ref,
                                expires_on_change=expires_on_change)


def _record_unlocked(root, context_id, *, kind, producer, result, summary, source_ref,
                     expires_on_change=None):
    try:
        ctx = context_store.load(root, context_id)
    except context_store.ContextError as error:
        raise EvidenceError(str(error)) from error
    if kind not in KINDS or result not in RESULTS:
        raise EvidenceError(f"未知证据类型或结果: {kind}/{result}")
    if not producer or not summary or not source_ref:
        raise EvidenceError("producer、summary、source_ref 必填")
    if expires_on_change is not None and expires_on_change is not True:
        raise EvidenceError("门禁证据不能关闭代码变化过期规则")
    expires_on_change = True
    item = {
        "evidence_id": f"{kind}-{uuid.uuid4().hex[:12]}", "context_id": context_id,
        "kind": kind, "producer": producer, "result": result, "summary": summary,
        "source_ref": source_ref, "code_fingerprint": code_fingerprint(root, ctx),
        "created_at": _now(), "expires_on_change": bool(expires_on_change), "status": "active",
    }
    path = _evidence_path(root, ctx["task_id"], kind)
    if not path.is_file():
        raise EvidenceError(f"目标阶段文档不存在: {path}")
    _append(path, item)
    return item


def _items_in(path, context_id):
    if not path.is_file():
        return []
    content = path.read_text(encoding="utf-8")
    if START not in content or END not in content:
        return []
    section = content.split(START, 1)[1].split(END, 1)[0]
    items = []
    keys = ("evidence_id", "context_id", "kind", "producer", "result", "summary", "source_ref",
            "code_fingerprint", "created_at", "expires_on_change", "status")
    for row in section.splitlines():
        if not row.startswith("| ") or row.startswith(("| ID ", "|:---")):
            continue
        cells = [value.strip().replace("\\|", "|") for value in re.split(r"(?<!\\)\|", row.strip("| "))]
        if len(cells) == 11 and cells[1] == context_id and cells[2] in KINDS:
            items.append(dict(zip(keys, cells)))
    return items


def list_all(root, context_id):
    ctx = context_store.load(root, context_id)
    paths = {_evidence_path(root, ctx["task_id"], kind) for kind in KINDS}
    items = [item for path in sorted(paths) for item in _items_in(path, context_id)]
    current = code_fingerprint(root, ctx)
    latest = {}
    for item in sorted(items, key=lambda row: (row["created_at"], row["evidence_id"])):
        previous = latest.get(item["kind"])
        if previous:
            previous["status"] = "superseded"
        latest[item["kind"]] = item
    for item in items:
        item["expires_on_change"] = item["expires_on_change"] == "True"
        if item["status"] == "active" and item["code_fingerprint"] != current:
            item["status"] = "stale"
    return items


def load(root, context_id, evidence_id):
    for item in list_all(root, context_id):
        if item["evidence_id"] == evidence_id:
            return item
    raise EvidenceError(f"证据不存在: {evidence_id}")


def refresh_staleness(root, context_id):
    return [item["evidence_id"] for item in list_all(root, context_id) if item["status"] == "stale"]


def valid_kinds(root, context_id):
    return {item["kind"] for item in list_all(root, context_id)
            if item["status"] == "active" and item["result"] == "pass"}
