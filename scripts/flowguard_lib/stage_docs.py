"""以 docs/ Markdown 为事实源的十阶段文档模型。"""
import datetime
import hashlib
import re
from pathlib import Path

from . import detect, ids, registry, state, validation

VALID_STATUSES = (
    "pending", "in_progress", "pending_acceptance", "accepted",
    "inherited", "skipped", "invalidated",
)
SATISFIED = ("accepted", "inherited", "skipped")

# 合法状态迁移表（单一事实源；测试做全矩阵断言）。
# invalidated 是指纹派生态：正文/前置变化后由 read() 推导，不可直接写入。
# 满足态之间禁止互跳与重复写：回改须显式退回 in_progress，重新走验收；
# 仅 invalidated（正文已变）可直接重新验收。
LEGAL = {
    "pending": ("in_progress", "accepted", "inherited", "skipped"),
    "in_progress": ("pending_acceptance", "accepted", "inherited", "skipped"),
    "pending_acceptance": ("in_progress", "accepted", "inherited", "skipped"),
    "invalidated": ("in_progress", "accepted", "inherited", "skipped"),
    "accepted": ("in_progress",),
    "inherited": ("in_progress",),
    "skipped": ("in_progress",),
}
FIELDS = ("任务", "父任务", "阶段", "阶段状态", "规格事实源", "原生产物", "批准依据")
_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", re.MULTILINE)


class StageDocError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def path_for(root, task_id, stage):
    if stage not in registry.ARTIFACTS:
        raise StageDocError(f"未知阶段: {stage}")
    if not ids.is_kebab(task_id):
        raise StageDocError(f"非法功能标识: {task_id}")
    art = registry.ARTIFACTS[stage]
    if art["scope"] == "project":
        return Path(root) / "docs" / "project" / f"{stage}.md"
    return Path(root) / "docs" / "features" / task_id / f"{stage}.md"


def _rows(text):
    return {key.strip(): value.strip() for key, value in _ROW.findall(text)}


def _metadata(ctx, stage, *, parent_task_id=None):
    return (
        "### 1.3 FlowGuard 阶段信息\n\n"
        "| 字段 | 值 |\n|:---|:---|\n"
        f"| 任务 | {ctx['task_id']} |\n"
        f"| 父任务 | {parent_task_id or '-'} |\n"
        f"| 阶段 | {stage} |\n"
        "| 阶段状态 | pending |\n"
        f"| 规格事实源 | {ctx.get('spec_system') or 'none'} |\n"
        f"| 原生产物 | {ctx.get('spec_ref') or '-'} |\n"
        "| 批准依据 | - |\n"
        "| 前置指纹 | - |\n"
        "| 验收指纹 | - |\n\n"
    )


def _content_hash(text):
    """阶段正文指纹不包含阶段状态行与可追加的检查证据表。"""
    text = re.sub(
        r"\n?<!-- FLOWGUARD_EVIDENCE_START -->.*?<!-- FLOWGUARD_EVIDENCE_END -->\n?",
        "", text, flags=re.DOTALL,
    )
    text = re.sub(r"^\| (阶段状态|批准依据|前置指纹|验收指纹) \|.*$", "", text, flags=re.MULTILINE)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _release_scope_features(root):
    """从项目发布文档的 Scope 表读取本次交付功能，空白或非法范围不可验收。"""
    path = Path(root) / "docs" / "project" / "10-release.md"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    section = re.search(
        r"(?ms)^## 3\. 发布内容[^\n]*\n(.*?)(?=^---\s*$|^## 4\.|\Z)",
        text,
    )
    if not section:
        return None
    features = []
    for line in section.group(1).splitlines():
        if not line.startswith("|"):
            continue
        columns = [
            part.strip().replace("\\|", "|")
            for part in re.split(r"(?<!\\)\|", line.strip().strip("|"))
        ]
        if len(columns) != 3:
            return None
        feature = columns[0]
        if feature in ("功能 (feature)", ":---", "---"):
            continue
        if not ids.is_kebab(feature) or feature in features:
            return None
        features.append(feature)
    return features or None


def _upstream_fingerprint(root, task_id, stage):
    """功能阶段记录所有前置阶段的验收指纹，项目共享文档不绑定单一功能。"""
    if stage == "10-release":
        features = _release_scope_features(root)
        if not features:
            return None
        standards = read(root, task_id, "07-standards")
        if standards["status"] not in SATISFIED:
            return None
        values = [f"07-standards:{standards['fingerprint']}"]
        for feature in features:
            docs = read(root, feature, "09-docs")
            if docs["status"] not in SATISFIED:
                return None
            values.append(f"{feature}/09-docs:{docs['fingerprint']}")
        return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()
    if registry.ARTIFACTS[stage]["scope"] == "project":
        return "project"
    predecessors = list(registry.ARTIFACTS)[:list(registry.ARTIFACTS).index(stage)]
    values = []
    for prior in predecessors:
        item = read(root, task_id, prior)
        if item["status"] not in SATISFIED:
            return None
        values.append(f"{prior}:{item['fingerprint']}")
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def ensure(root, ctx, *, parent_task_id=None):
    """创建缺失的阶段文档；已存在文档保持原样。"""
    from templates import artifacts

    created = []
    for stage in registry.ARTIFACTS:
        path = path_for(root, ctx["task_id"], stage)
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = artifacts.render(stage, {
            "feature": ctx["task_id"], "title": ctx["task_id"],
            "modules": "-", "req_prefix": f"{ctx['task_id']}/REQ",
        })
        marker = "\n---\n\n## 2."
        if marker not in rendered:
            raise StageDocError(f"模板缺少第二章: {stage}")
        rendered = rendered.replace(marker, "\n" + _metadata(ctx, stage, parent_task_id=parent_task_id) + marker, 1)
        state.atomic_create_text(path, rendered)
        created.append(str(path.relative_to(root)))
    return created


def ensure_project(root):
    """只创建项目级的 02、07、10 文档。"""
    with state.state_lock(root):
        return _ensure_project_unlocked(root)


def _ensure_project_unlocked(root):
    from templates import artifacts

    root = Path(root)
    task = {"task_id": root.resolve().name, "spec_system": "none", "spec_ref": None}
    created = []
    for stage, art in registry.ARTIFACTS.items():
        if art["scope"] != "project":
            continue
        path = root / "docs" / "project" / f"{stage}.md"
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        text = artifacts.render(stage, {"feature": task["task_id"], "title": task["task_id"], "modules": "-"})
        marker = "\n---\n\n## 2."
        text = text.replace(marker, "\n" + _metadata(task, stage) + marker, 1)
        state.atomic_create_text(path, text)
        created.append(str(path.relative_to(root)))
    return created


def read(root, task_id, stage):
    path = path_for(root, task_id, stage)
    if not path.is_file():
        return {"stage": stage, "status": "pending", "path": str(path.relative_to(root)), "missing": True}
    rows = _rows(path.read_text(encoding="utf-8"))
    if rows.get("阶段") != stage or rows.get("阶段状态") not in VALID_STATUSES:
        raise StageDocError(f"阶段元信息缺失或非法: {path}")
    status = rows["阶段状态"]
    fingerprint = rows.get("验收指纹", "-")
    if status in SATISFIED:
        if fingerprint != _content_hash(path.read_text(encoding="utf-8")):
            status = "invalidated"
        elif rows.get("前置指纹") != _upstream_fingerprint(root, task_id, stage):
            status = "invalidated"
    return {
        "stage": stage, "status": status, "path": str(path.relative_to(root)),
        "approval_ref": rows.get("批准依据", "-"), "spec_ref": rows.get("原生产物", "-"),
        "fingerprint": fingerprint,
        "missing": False,
    }


def snapshot(root, task_id):
    requirement = path_for(root, task_id, "01-requirements")
    if not requirement.is_file():
        raise StageDocError(f"功能文档不存在: {task_id}")
    rows = _rows(requirement.read_text(encoding="utf-8"))
    if rows.get("任务") != task_id:
        raise StageDocError(f"功能文档标识不匹配: {requirement}")
    return {
        "context": {
            "task_id": task_id,
            "parent_task_id": None if rows.get("父任务") in (None, "-") else rows["父任务"],
            "spec_system": rows.get("规格事实源"),
            "spec_ref": rows.get("原生产物"),
        },
        "stages": {stage: read(root, task_id, stage) for stage in registry.ARTIFACTS},
    }


def recoverable(root):
    """只读扫描 docs/，供会话缓存丢失后重新绑定任务。"""
    root = Path(root)
    project = {}
    for stage, artifact in registry.ARTIFACTS.items():
        if artifact["scope"] != "project":
            continue
        try:
            item = read(root, "project", stage)
            if not item["missing"]:
                project[stage] = item["status"]
        except StageDocError:
            project[stage] = "invalid"
    tasks = []
    directory = root / "docs" / "features"
    if directory.is_dir():
        for requirement in sorted(directory.glob("*/01-requirements.md")):
            task_id = requirement.parent.name
            if not ids.is_kebab(task_id):
                continue
            try:
                data = snapshot(root, task_id)
                next_stage = next(
                    (stage for stage, item in data["stages"].items() if item["status"] not in SATISFIED),
                    None,
                )
                tasks.append({
                    "task_id": task_id,
                    "parent_task_id": data["context"]["parent_task_id"],
                    "next_stage": next_stage,
                })
            except StageDocError as error:
                tasks.append({"task_id": task_id, "error": str(error)})
    return {"project": project, "tasks": tasks}


def missing_before(root, task_id, action):
    target = {
        "code_write": 7,
        "git_commit": 9,
        "release": 10,
    }.get(action, 0)
    return [
        stage for stage in list(registry.ARTIFACTS)[:target]
        if read(root, task_id, stage)["status"] not in SATISFIED
    ]


def advance(root, task_id, stage, target, *, approval_ref=None, reason=None):
    with state.state_lock(root):
        return _advance_unlocked(
            root, task_id, stage, target, approval_ref=approval_ref, reason=reason,
        )


def _advance_unlocked(root, task_id, stage, target, *, approval_ref=None, reason=None):
    if target not in VALID_STATUSES or target == "pending":
        raise StageDocError(f"非法目标状态: {target}")
    path = path_for(root, task_id, stage)
    current = read(root, task_id, stage)
    if current["missing"]:
        raise StageDocError(f"阶段文档不存在: {path}")
    allowed = LEGAL.get(current["status"], ())
    if target not in allowed:
        raise StageDocError(
            f"非法状态迁移 {current['status']} → {target}"
            f"（合法目标: {', '.join(allowed) or '无'}）")
    if target in SATISFIED and not approval_ref:
        raise StageDocError("验收、继承或跳过必须提供批准依据；理由文本不能代替批准")
    if target in ("inherited", "skipped") and not reason:
        raise StageDocError("继承或跳过必须说明理由及适用范围")
    if target == "accepted":
        body = path.read_text(encoding="utf-8")
        if re.search(r"\{\{[^}\n]+\}\}", body):
            raise StageDocError(f"阶段文档仍含占位符: {path}")
        if stage == "01-requirements":
            if not validation.requirement_ids(body):
                raise StageDocError("需求文档缺少可验证的 REQ-ID")
            issues = validation.validate_requirements(body, task_id)
        elif stage == "04-testcases":
            requirements = path_for(root, task_id, "01-requirements").read_text(encoding="utf-8")
            req_ids = validation.requirement_ids(requirements)
            if not req_ids:
                raise StageDocError("测试用例缺少有效需求作为追溯来源")
            issues = validation.validate_testcases(body, req_ids, root)
        elif stage == "08-review":
            issues = validation.validate_review(body)
        elif stage == "02-architecture":
            issues = validation.validate_architecture(body)
        elif stage == "07-standards":
            issues = validation.validate_standards(body, detect.detect(root)["modules"])
        elif stage == "10-release":
            issues = validation.validate_release(body, validation.known_task_ids(root))
        else:
            issues = []
        blocking = [item["message"] for item in issues if item["level"] in ("ERROR", "WARNING")]
        if blocking:
            raise StageDocError("阶段文档校验未通过: " + "; ".join(blocking))
        predecessors = list(registry.ARTIFACTS).index(stage)
        unsatisfied = [
            prior for prior in list(registry.ARTIFACTS)[:predecessors]
            if read(root, task_id, prior)["status"] not in SATISFIED
        ]
        if unsatisfied:
            raise StageDocError("前置阶段尚未满足: " + ", ".join(unsatisfied))
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"^\| 阶段状态 \| [^|]* \|$", f"| 阶段状态 | {target} |", text,
        count=1, flags=re.MULTILINE,
    )
    if approval_ref or reason:
        text = re.sub(
            r"^\| 批准依据 \| [^|]* \|$",
            f"| 批准依据 | {approval_ref or reason} |", text,
            count=1, flags=re.MULTILINE,
        )
    if target in SATISFIED:
        upstream = _upstream_fingerprint(root, task_id, stage)
        if upstream is None:
            raise StageDocError("前置阶段尚未满足，不能验收、继承或跳过")
        if re.search(r"^\| 前置指纹 \| [^|]* \|$", text, flags=re.MULTILINE):
            text = re.sub(
                r"^\| 前置指纹 \| [^|]* \|$", f"| 前置指纹 | {upstream} |", text,
                count=1, flags=re.MULTILINE,
            )
        else:
            text = text.replace("| 验收指纹 |", f"| 前置指纹 | {upstream} |\n| 验收指纹 |", 1)
        digest = _content_hash(text)
        text = re.sub(
            r"^\| 验收指纹 \| [^|]* \|$", f"| 验收指纹 | {digest} |", text,
            count=1, flags=re.MULTILINE,
        )
    state.atomic_write_text(path, text)
    return read(root, task_id, stage)
