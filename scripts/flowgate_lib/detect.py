"""技术栈与模块探测（spec §3.2/§7）。"""
import datetime
import json
import re
from pathlib import Path

from .ids import is_kebab

MARKERS = [
    ("pom.xml", "java-spring"), ("build.gradle", "java-spring"), ("build.gradle.kts", "java-spring"),
    ("package.json", "node"), ("Cargo.toml", "rust"), ("go.mod", "go"),
]
PRUNE = {".git", "node_modules", "target", "dist", "build", ".idea", "vendor", ".venv", "__pycache__"}
MAX_DEPTH = 4


def _kebab(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "app"


def _stack_of(dirpath, marker, marker_stack):
    if marker == "package.json":
        try:
            pkg = json.loads((dirpath / marker).read_text(encoding="utf-8"))
        except Exception:
            return "node"
        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        if any(d.startswith("vue") for d in deps):
            return "vue3"
        if any(d.startswith("react") for d in deps):
            return "react"
        return "node"
    return marker_stack


def detect(root):
    root = Path(root)
    modules = {}
    base = root.resolve()
    for dirpath, dirnames, filenames in _walk(base):
        rel = dirpath.relative_to(base)
        for marker, marker_stack in MARKERS:
            if marker not in filenames:
                continue
            name = "app" if rel == Path(".") else _kebab(dirpath.name)
            if name not in modules:
                src_root = "." if rel == Path(".") else str(rel)
                modules[name] = {"src_roots": [src_root],
                                 "stack": _stack_of(dirpath, marker, marker_stack)}
            break
    if not modules:
        modules = {"app": {"src_roots": ["."], "stack": None}}

    stacks = [m["stack"] for m in modules.values()]
    backend = next((s for s in stacks if s in ("java-spring", "rust", "go")), None)
    frontend = next((s for s in stacks if s in ("vue3", "react", "node")), None)
    return {
        "stack": {"backend": backend, "frontend": frontend,
                  "detected_at": datetime.datetime.now(datetime.timezone.utc).isoformat()},
        "modules": modules,
    }


def _walk(base):
    """os.walk + 剪枝 + 深度上限。"""
    for dirpath, dirnames, filenames in Path(base).walk():
        rel = Path(dirpath).relative_to(base)
        depth = len(rel.parts)
        if depth >= MAX_DEPTH:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        yield Path(dirpath), dirnames, filenames


def init_project(root):
    """建 .flowgate/ 骨架（实现在 templates/artifacts.py，此处委托保持单入口）。"""
    from ..templates.artifacts import init_project as _init
    return _init(root)
