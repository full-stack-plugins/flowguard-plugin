#!/usr/bin/env python3
"""Stop：汇总治理上下文、缺失证据和兼容状态，不把会话结束当作任务完成。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import context, discovery, evidence, governance, stage_docs, state  # noqa: E402

FEATURE_STAGES = ("requirements", "solution", "testcases", "hld", "lld", "review", "docs")
OK = ("accepted", "skipped", "overridden")


def _emit(lines):
    message = "\n".join(lines)
    print(json.dumps({"systemMessage": message} if message else {}, ensure_ascii=False))


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
        try:
            active = context.active(cwd, session_id)
        except Exception as error:
            active = None
            lines.append(f"[flowguard] WARNING: 上下文恢复失败，按未绑定处理: {error}")
        if active:
            if active["task_type"] != "read_only":
                try:
                    missing_stages = stage_docs.missing_before(cwd, active["task_id"], "release")
                    if missing_stages:
                        lines.append(f"[flowguard] 十阶段 docs 下一步: {missing_stages[0]}（stage status --task-id {active['task_id']}）")
                    else:
                        lines.append("[flowguard] 十阶段 docs 已满足；仍需复核证据与用户验收")
                except stage_docs.StageDocError as error:
                    lines.append(f"[flowguard] 十阶段 docs 状态不可读: {error}")
            current_evidence = evidence.list_all(cwd, active["context_id"])
            valid = {item["kind"] for item in current_evidence
                     if item["status"] == "active" and item["result"] == "pass"}
            missing = [kind for kind in governance.COMMIT_EVIDENCE if kind not in valid]
            lines.append(
                f"[flowguard] 本轮上下文 {active['task_id']}({active['task_type']}) "
                f"| 状态={active['status']}"
            )
            if missing:
                lines.append(f"[flowguard] 缺失提交证据: {', '.join(missing)}")
                other_checks = [kind for kind in missing if kind != "semantic_review"]
                if other_checks:
                    lines.append(
                        f"[flowguard] 下一步: 执行真实检查并登记 {', '.join(other_checks)} 的当前代码指纹证据"
                    )
                if "semantic_review" in missing:
                    advisory = any(
                        item["kind"] == "semantic_review"
                        and item["producer"] == "hook:codereview-cli"
                        and item["result"] == "warning"
                        and item["status"] == "active"
                        for item in current_evidence
                    )
                    if advisory:
                        lines.append("[flowguard] 下一步: CodeReview 建议性回执仍是 WARNING；接入可信放行依据前保持提交阻断，不得手工录入 PASS")
                    else:
                        lines.append("[flowguard] 下一步: 获取结构化 CodeReview 回执并按可信审查策略校验；不得手工录入 PASS")
            else:
                lines.append("[flowguard] 提交证据已齐；提交前仍需运行 governance --action git_commit 复核")
        else:
            lines.append("[flowguard] 本轮尚未绑定治理上下文；下轮先完成任务分类与 context bind")
    try:
        project = state.load_project(cwd)
    except Exception:
        project = None
    if not project:
        _emit(lines)
        return 0
    fid = project.get("current_feature")
    if fid:
        try:
            f = state.load_feature(cwd, fid)
            nxt = next((s for s in FEATURE_STAGES if f["stages"][s]["status"] not in OK), None)
            if f.get("status") == "active":
                if nxt:
                    lines.append(f"[flowguard] 兼容功能 {fid} 下一步: 阶段 {nxt}（/flowguard-next）")
                else:
                    lines.append(f"[flowguard] 兼容功能 {fid} 全阶段已收敛，可 /flowguard-feature done {fid}")
        except Exception:
            pass
    pending = [s for s in ("architecture", "standards", "release")
               if project["stages"][s]["status"] not in OK]
    if pending:
        lines.append(f"[flowguard] 兼容项目级待推进: {', '.join(pending)}（/flowguard-next --stage {pending[0]}）")
    active = [k for k, v in (project.get("features") or {}).items() if v.get("status") == "active"]
    if not active and not pending:
        lines.append("[flowguard] 兼容十阶段全部收敛；新任务仍须以治理上下文和当前证据复核")
    _emit(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
