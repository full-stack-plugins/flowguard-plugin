#!/usr/bin/env python3
"""SessionStart：注入流程状态摘要（未初始化则静默）。协议见 hooks/__protocol__.md。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import state  # noqa: E402

FEATURE_STAGES = ("requirements", "solution", "testcases", "hld", "lld", "review", "docs")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    cwd = Path(payload.get("cwd") or os.getcwd())
    try:
        project = state.load_project(cwd)
    except Exception:
        return 0  # 未初始化：静默
    lines = [f"[flowguard] 项目 {project['project']} | current_feature: {project.get('current_feature') or '未设定'}"]
    lines.append("[flowguard] 项目级阶段: " + ", ".join(
        f"{s}={project['stages'][s]['status']}" for s in ("architecture", "standards", "release")))
    for fid in (project.get("features") or {}):
        try:
            f = state.load_feature(cwd, fid)
        except Exception:
            continue
        sts = " ".join(f"{s[0]}={f['stages'][s]['status']}" for s in FEATURE_STAGES)
        lines.append(f"[flowguard] 功能 {fid}({f.get('status')}): {sts}")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
