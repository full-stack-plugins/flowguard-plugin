#!/usr/bin/env python3
"""PreToolUse：按治理上下文校验写码、提交与发布；旧状态仅作兼容。"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import discovery, gate, governance, registry  # noqa: E402


def _relative(cwd, path):
    if not path:
        return ""
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(Path(cwd).resolve())
        except ValueError:
            return str(candidate).replace("\\", "/")
    normalized = str(candidate).replace("\\", "/")
    return normalized[2:] if normalized.startswith("./") else normalized


def _write_action(cwd, path):
    rel = _relative(cwd, path)
    if rel.startswith((".specify/", "openspec/", "docs/superpowers/")):
        return "spec_write"
    if rel.startswith(".flowguard/") and (
        "/artifacts/" in rel or rel.startswith(".flowguard/project/")
    ):
        return "spec_write"  # 旧产物兼容：允许补规格以解除阻断
    parts = Path(rel).parts
    name = Path(rel).name.lower()
    if (
        any(part.lower() in ("test", "tests", "__tests__") for part in parts)
        or name.startswith("test_")
        or "_test." in name
        or ".test." in name
        or ".spec." in name
    ):
        return "test_write"
    return "code_write"


def _protected_governance_path(cwd, path):
    rel = _relative(cwd, path)
    return rel.startswith((
        ".flowguard/contexts/", ".flowguard/evidence/", ".flowguard/journal/",
    )) or rel in (".flowguard/project.json",)


def _print_denial(env):
    print(f"ERROR: {env['message']}", file=sys.stderr)
    print(f"Fix: {env['fix']}", file=sys.stderr)
    if env.get("missing"):
        print(f"Missing: {', '.join(env['missing'])}", file=sys.stderr)
    if env.get("allowed_actions"):
        print(f"Allowed: {', '.join(env['allowed_actions'])}", file=sys.stderr)
    print(f"[flowguard] code={env['code']}", file=sys.stderr)


def _is_git_commit(command):
    pattern = (
        r"(?:^|[;&|]\s*)"
        r"(?:command\s+)?(?:\S+/)?git"
        r"(?:\s+(?:(?:-C|--git-dir|--work-tree)\s+\S+|(?:--git-dir|--work-tree)=\S+))*"
        r"\s+commit\b"
    )
    return bool(re.search(pattern, command, re.IGNORECASE))


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("WARNING: flowguard_gate 收到非法 stdin，放行", file=sys.stderr)
        return 0
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()

    session_id = payload.get("session_id") or payload.get("conversation_id") or "default"
    action, path = None, None
    if tool in ("Write", "Edit", "MultiEdit"):
        path = tool_input.get("file_path")
        if not path:
            print("WARNING: flowguard_gate 缺少 file_path，异常放行", file=sys.stderr)
            return 0
        if _protected_governance_path(cwd, path):
            _print_denial({
                "code": "governance_state_protected",
                "message": "FlowGuard 治理状态禁止通过文件编辑工具直接修改",
                "fix": "使用 context/evidence/legacy CLI 变更状态，以保留校验和审计记录",
                "missing": [],
                "allowed_actions": ["read", "spec_write"],
            })
            return 2
        action = _write_action(cwd, path)
    elif tool == "Bash":
        cmd = (tool_input.get("command") or "").lower()
        if _is_git_commit(cmd):
            action = "git_commit"
        elif any(pat in cmd for pat in registry.RELEASE_CMD_PATTERNS):
            action = "release"
        else:
            return 0  # 非构建/发布命令不归门禁管
    else:
        return 0

    try:
        snapshot = discovery.discover(Path(cwd))
        if snapshot["git"]["is_repository"]:
            res = governance.evaluate(Path(cwd), action, session_id=session_id, path=path)
        elif (Path(cwd) / ".flowguard" / "project.json").exists():
            legacy_action = "build_release" if action == "release" else "write_code"
            res = gate.check_action(Path(cwd), legacy_action, path=path)
        else:
            return 0
    except Exception as e:  # 钩子自身崩溃 = 放行 + 警告
        print(f"WARNING: flowguard_gate 异常放行: {e}", file=sys.stderr)
        return 0
    if res["allowed"]:
        return 0
    env = res["envelope"]
    _print_denial(env)
    return 2


if __name__ == "__main__":
    sys.exit(main())
