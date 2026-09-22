#!/usr/bin/env python3
"""Stop：阶段小结与下一步提示（未初始化则静默）。协议见 hooks/__protocol__.md。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import state  # noqa: E402

FEATURE_STAGES = ("requirements", "solution", "testcases", "hld", "lld", "review", "docs")
OK = ("accepted", "skipped", "overridden")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    cwd = Path(payload.get("cwd") or os.getcwd())
    try:
        project = state.load_project(cwd)
    except Exception:
        return 0
    fid = project.get("current_feature")
    if fid:
        try:
            f = state.load_feature(cwd, fid)
            nxt = next((s for s in FEATURE_STAGES if f["stages"][s]["status"] not in OK), None)
            if f.get("status") == "active":
                if nxt:
                    print(f"[flowguard] 功能 {fid} 下一步: 阶段 {nxt}（/flowguard-next）")
                else:
                    print(f"[flowguard] 功能 {fid} 全阶段已收敛，可 /flowguard-feature done {fid}")
        except Exception:
            pass
    pending = [s for s in ("architecture", "standards", "release")
               if project["stages"][s]["status"] not in OK]
    if pending:
        print(f"[flowguard] 项目级待推进: {', '.join(pending)}（/flowguard-next --stage {pending[0]}）")
    active = [k for k, v in (project.get("features") or {}).items() if v.get("status") == "active"]
    if not active and not pending:
        print("[flowguard] 全部收敛，可进入部署交付（/flowguard-next --stage release）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
