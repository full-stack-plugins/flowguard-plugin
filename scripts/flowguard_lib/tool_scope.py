"""跨 Hook 共用的工具目标 worktree 校验。"""
from pathlib import Path

from . import discovery


def same_git_worktree(cwd, target, *, expected_root=None):
    """显式目标必须属于当前 Git worktree；非法路径一律不匹配。"""
    if not isinstance(target, str) or not target.strip():
        return False
    try:
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        current_root = expected_root or discovery.discover(cwd)["git"]["root"]
        target_root = discovery.discover(candidate)["git"]["root"]
        return bool(current_root) and target_root == current_root
    except (OSError, ValueError):
        return False
