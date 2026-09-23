"""把旧阶段正文复制到 docs/，保留旧数据以供核对。"""
import json
import re
import stat
from pathlib import Path

from . import ids, registry, stage_docs, state


class MigrationError(Exception):
    pass


def _legacy_status(root, task_id, stage):
    if registry.ARTIFACTS[stage]["scope"] == "project":
        path = Path(root) / ".flowguard" / "project.json"
    else:
        path = Path(root) / ".flowguard" / "features" / task_id / "state.json"
    if not path.is_file():
        return "pending"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("stages", {}).get(registry.ARTIFACTS[stage]["stage"], {}).get("status", "pending")
    except (OSError, json.JSONDecodeError) as error:
        raise MigrationError(f"旧状态不可读: {path}") from error


def preview(root):
    root = Path(root).resolve()
    legacy = root / ".flowguard"
    entries = []
    for stage, art in registry.ARTIFACTS.items():
        if art["scope"] == "project":
            sources = [("project", legacy / "project" / f"{stage}.md")]
        else:
            sources = [(path.name, path / "artifacts" / f"{stage}.md")
                       for path in sorted((legacy / "features").glob("*")) if path.is_dir()]
        for task_id, source in sources:
            if not source.is_file():
                continue
            if not ids.is_kebab(task_id):
                raise MigrationError(f"旧功能标识非法，需人工处理: {task_id}")
            destination = stage_docs.path_for(root, task_id, stage)
            entries.append({
                "source": str(source.relative_to(root)),
                "destination": str(destination.relative_to(root)),
                "task_id": task_id, "stage": stage,
                "legacy_status": _legacy_status(root, task_id, stage),
            })
    conflicts = [item["destination"] for item in entries if (root / item["destination"]).exists()]
    return {"entries": entries, "conflicts": conflicts, "created": []}


def _with_metadata(text, item):
    source = item["source"]
    old = item["legacy_status"]
    new_status = "in_progress" if old == "in_progress" else "pending_acceptance" if old in (
        "accepted", "skipped", "overridden", "pending_acceptance",
    ) else "pending"
    ctx = {"task_id": item["task_id"], "spec_system": "none", "spec_ref": None}
    metadata = stage_docs._metadata(ctx, item["stage"])
    metadata = metadata.replace("| 阶段状态 | pending |", f"| 阶段状态 | {new_status} |")
    metadata = metadata.replace("| 批准依据 | - |", f"| 批准依据 | 待复核；旧状态 {old} |")
    metadata += f"| 迁移来源 | {source} |\n\n"
    match = re.search(r"^## 2\.", text, flags=re.MULTILINE)
    if match:
        return text[:match.start()] + metadata + text[match.start():]
    return text.rstrip() + "\n\n" + metadata


def apply(root):
    with state.state_lock(root):
        return _apply_unlocked(root)


def _apply_unlocked(root):
    root = Path(root).resolve()
    plan = preview(root)
    if plan["conflicts"]:
        raise MigrationError("目标文档冲突，未写入任何文件: " + ", ".join(plan["conflicts"]))
    created = []
    try:
        for item in plan["entries"]:
            source = root / item["source"]
            target = root / item["destination"]
            target.parent.mkdir(parents=True, exist_ok=True)
            text = _with_metadata(source.read_text(encoding="utf-8"), item)
            state.atomic_create_text(
                target, text, mode=stat.S_IMODE(source.stat().st_mode),
            )
            created.append(target)
    except Exception as error:
        kept = [str(target.relative_to(root)) for target in created]
        detail = "、".join(kept) if kept else "无"
        raise MigrationError(
            f"迁移中断；已创建文档保留供核对: {detail}；未移除旧数据。原因: {error}"
        ) from error
    plan["created"] = [str(target.relative_to(root)) for target in created]
    return plan
