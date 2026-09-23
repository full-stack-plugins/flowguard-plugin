"""Git 与原生 SDD 体系的只读发现。

发现只报告事实，不初始化项目、不安装工具，也不替智能体完成语义选择。
"""
import hashlib
import shutil
import subprocess
from pathlib import Path


def _git(root, *args):
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _relative_paths(root, pattern):
    return sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.glob(pattern)
        if path.is_dir() or path.is_file()
    )


def _project_type(root, is_repository):
    if not is_repository:
        return "unknown"
    commit_count = _git(root, "rev-list", "--count", "HEAD")
    if commit_count and int(commit_count) > 0:
        return "brownfield"
    source_markers = (
        "src", "app", "server", "web", "pom.xml", "build.gradle", "package.json",
        "Cargo.toml", "pyproject.toml", "requirements.txt", "go.mod",
    )
    return "brownfield" if any((root / item).exists() for item in source_markers) else "greenfield"


def discover(start):
    """返回项目、Git、SDD 标识与工具可用性的结构化快照。"""
    start = Path(start).resolve()
    probe = start.parent if start.is_file() else start
    git_root_text = _git(probe, "rev-parse", "--show-toplevel")
    is_repository = bool(git_root_text)
    root = Path(git_root_text).resolve() if git_root_text else probe
    common_text = _git(root, "rev-parse", "--git-common-dir") if is_repository else None
    if common_text:
        common = Path(common_text)
        common = (root / common).resolve() if not common.is_absolute() else common.resolve()
    else:
        common = None
    worktree_seed = f"{root}|{common or ''}"
    worktree_id = hashlib.sha256(worktree_seed.encode("utf-8")).hexdigest()[:16]

    markers = {
        "spec-kit": (root / ".specify").is_dir(),
        "openspec": (root / "openspec").is_dir(),
        "superpowers": (
            (root / "docs" / "superpowers" / "specs").is_dir()
            or (root / "docs" / "superpowers" / "plans").is_dir()
        ),
    }
    artifacts = []
    if markers["spec-kit"]:
        artifacts.extend(_relative_paths(root, ".specify/specs/*"))
    if markers["openspec"]:
        artifacts.extend(_relative_paths(root, "openspec/changes/*"))
    if markers["superpowers"]:
        artifacts.extend(_relative_paths(root, "docs/superpowers/specs/*.md"))
        artifacts.extend(_relative_paths(root, "docs/superpowers/plans/*.md"))

    formal = [name for name in ("spec-kit", "openspec") if markers[name]]
    conflicts = list(formal) if len(formal) > 1 else []
    if conflicts:
        selected, status = None, "choice_required"
    elif formal:
        selected, status = formal[0], "ready"
    elif markers["superpowers"]:
        selected, status = "superpowers", "ready"
    elif is_repository:
        selected, status = None, "assessment_required"
    else:
        selected, status = None, "not_git"

    return {
        "root": str(root),
        "project_type": _project_type(root, is_repository),
        "git": {
            "is_repository": is_repository,
            "root": str(root) if is_repository else None,
            "common_dir": str(common) if common else None,
            "worktree_id": worktree_id,
        },
        "sdd": {
            "status": status,
            "selected_system": selected,
            "markers": markers,
            "artifacts": sorted(set(artifacts)),
            "conflicts": conflicts,
        },
        "tools": {
            "specify_cli": bool(shutil.which("specify")),
            "openspec_cli": bool(shutil.which("openspec")),
        },
    }
