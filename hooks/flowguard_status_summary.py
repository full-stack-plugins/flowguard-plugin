#!/usr/bin/env python3
"""SessionStart：只读发现 SDD 状态并恢复治理上下文。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import context, discovery, stage_docs, state  # noqa: E402

FEATURE_STAGES = ("requirements", "solution", "testcases", "hld", "lld", "review", "docs")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    cwd = Path(payload.get("cwd") or os.getcwd())
    session_id = payload.get("session_id") or payload.get("conversation_id") or "default"
    snapshot = discovery.discover(cwd)
    lines = []
    if snapshot["git"]["is_repository"]:
        sdd = snapshot["sdd"]
        lines.extend([
            "[flowguard] SDD 检测:",
            f"[flowguard] 项目类型={snapshot['project_type']} | 状态={sdd['status']}",
            f"[flowguard] 检测体系={', '.join(k for k, v in sdd['markers'].items() if v) or '无'}",
            f"[flowguard] 规格事实源={sdd['selected_system'] or '待智能体判断'}",
        ])
        if sdd["status"] == "choice_required":
            lines.append("[flowguard] 必须事项: Spec Kit 与 OpenSpec 冲突，写码前请用户选择本次变更事实源")
        elif sdd["status"] == "assessment_required":
            lines.append("[flowguard] 必须事项: 智能体需分类任务；重要变更须提出 SDD 选择并在初始化前取得批准")
        try:
            active = context.active(cwd, session_id)
        except Exception as error:
            active = None
            lines.append(f"[flowguard] WARNING: 上下文恢复失败，按未绑定处理: {error}")
        if active:
            lines.append(
                f"[flowguard] 当前上下文={active['task_id']}({active['task_type']}) "
                f"| source={active['spec_system']}:{active.get('spec_ref') or '-'}"
            )
            if active["task_type"] != "read_only":
                try:
                    missing = stage_docs.missing_before(cwd, active["task_id"], "release")
                    lines.append(f"[flowguard] 十阶段 docs 状态: {'下一步 ' + missing[0] if missing else '全部满足'}")
                except stage_docs.StageDocError as error:
                    lines.append(f"[flowguard] 十阶段 docs 状态不可读: {error}")
        else:
            lines.append("[flowguard] 当前上下文=未绑定 | 下一步: flowguard_state.py context bind ...")
            recovered = stage_docs.recoverable(cwd)
            if recovered["project"]:
                stages = ", ".join(f"{stage}={status}" for stage, status in recovered["project"].items())
                lines.append(f"[flowguard] 项目阶段: {stages}")
            for task in recovered["tasks"]:
                if task.get("error"):
                    lines.append(f"[flowguard] 可恢复任务 {task['task_id']}: 待修复 {task['error']}")
                else:
                    lines.append(
                        f"[flowguard] 可恢复任务 {task['task_id']} "
                        f"| parent={task['parent_task_id'] or '-'} "
                        f"| 下一步={task['next_stage'] or '全部满足'}"
                    )
    try:
        project = state.load_project(cwd)
    except Exception:
        project = None
    if project:
        lines.append(
            f"[flowguard] 兼容状态: 项目 {project['project']} | "
            f"legacy current_feature={project.get('current_feature') or '未设定'}"
        )
        for fid in (project.get("features") or {}):
            try:
                f = state.load_feature(cwd, fid)
            except Exception:
                continue
            sts = " ".join(f"{s[0]}={f['stages'][s]['status']}" for s in FEATURE_STAGES)
            lines.append(f"[flowguard] 兼容功能 {fid}({f.get('status')}): {sts}")
    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
