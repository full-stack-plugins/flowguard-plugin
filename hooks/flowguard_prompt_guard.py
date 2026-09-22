#!/usr/bin/env python3
"""UserPromptSubmit：提醒智能体重新判断任务、范围和上下文，不做关键词裁决。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import context, discovery  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    cwd = Path(payload.get("cwd") or os.getcwd())
    snapshot = discovery.discover(cwd)
    if not snapshot["git"]["is_repository"]:
        return 0
    session_id = payload.get("session_id") or payload.get("conversation_id") or "default"
    try:
        active = context.active(cwd, session_id)
    except Exception as error:
        active = None
        print(f"[flowguard] WARNING: 上下文恢复失败，按未绑定处理: {error}", file=sys.stderr)
    print("[flowguard] 请重新判断任务类型、目标仓库、范围变化与规格事实源；不要仅凭本 Hook 推断语义。")
    if active:
        print(
            f"[flowguard] 已绑定 {active['task_id']}({active['task_type']})；"
            "若本轮改变任务或范围，请重新执行 context bind。"
        )
    else:
        print("[flowguard] 尚无本会话上下文；完成只读发现后执行 context bind，重要变更先处理用户批准。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
