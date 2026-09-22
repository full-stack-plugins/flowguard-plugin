#!/usr/bin/env python3
"""PreToolUse 硬门禁（exit 2 阻断）。协议见 hooks/__protocol__.md。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import gate, registry  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("WARNING: flowguard_gate 收到非法 stdin，放行", file=sys.stderr)
        return 0
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()

    action, path = None, None
    if tool in ("Write", "Edit", "MultiEdit"):
        action, path = "write_code", tool_input.get("file_path")
    elif tool == "Bash":
        cmd = (tool_input.get("command") or "").lower()
        if any(pat in cmd for pat in registry.RELEASE_CMD_PATTERNS):
            action = "build_release"
        else:
            return 0  # 非构建/发布命令不归门禁管
    else:
        return 0

    try:
        res = gate.check_action(Path(cwd), action, path=path)
    except Exception as e:  # 钩子自身崩溃 = 放行 + 警告
        print(f"WARNING: flowguard_gate 异常放行: {e}", file=sys.stderr)
        return 0
    if res["allowed"]:
        return 0
    env = res["envelope"]
    print(f"ERROR: {env['message']}", file=sys.stderr)
    print(f"Fix: {env['fix']}", file=sys.stderr)
    print(f"[flowguard] code={env['code']}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
