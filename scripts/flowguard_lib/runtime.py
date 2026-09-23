"""宿主侧运行时缓存路径；项目流程事实始终保存在 docs/。"""
import hashlib
import os
import sys
from pathlib import Path


def repository_state_dir(root, *, create=False):
    override = os.environ.get("FLOWGUARD_STATE_HOME")
    if override:
        base = Path(override).expanduser()
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "FlowGuard"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "FlowGuard"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "flowguard"
    repository_id = hashlib.sha256(str(Path(root).resolve()).encode("utf-8")).hexdigest()[:20]
    path = base / repository_id
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path
