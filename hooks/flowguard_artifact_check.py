#!/usr/bin/env python3
"""PostToolUse：证据采集/失效 + 旧产物校验与降级（恒 exit 0）。"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import context, evidence, journal, state, validation  # noqa: E402

# artifact 文件名 → 阶段（用于降级与校验路由）
ARTIFACT_STAGE = {
    "01-requirements": "requirements", "02-architecture": "architecture",
    "03-solution": "solution", "04-testcases": "testcases",
    "05-hld": "hld", "06-lld": "lld", "07-standards": "standards",
    "08-review": "review", "09-docs": "docs", "10-release": "release",
}

TEST_COMMANDS = ("pytest", "unittest", "mvn test", "gradle test", "npm test", "pnpm test", "cargo test")
STATIC_COMMANDS = (
    "codeguard check", "codeguard-check", "codeguard-java", "codeguard-security-code",
    " lint", "eslint", "clippy", "checkstyle", "spotbugs", "ruff check",
)
REVIEW_COMMANDS = ("codereview", "code-review")


def _evidence_kind(command):
    command = f" {command.lower()} "
    if any(pattern in command for pattern in TEST_COMMANDS):
        return "tests"
    if any(pattern in command for pattern in STATIC_COMMANDS):
        return "static_analysis"
    if any(pattern in command for pattern in REVIEW_COMMANDS):
        return "semantic_review"
    return None


def _exit_code(payload):
    response = payload.get("tool_response") or payload.get("tool_result") or {}
    if isinstance(response, dict) and isinstance(response.get("exit_code"), int):
        return response["exit_code"]
    return None


def _parse_artifact(path):
    """返回 (scope, feature_id|None, stage) 或 None。"""
    p = str(path).replace("\\", "/")
    marker = ".flowguard/"
    if marker not in p or not p.endswith(".md"):
        return None
    rel = p.split(marker, 1)[1]
    if rel.startswith("features/"):
        parts = rel.split("/")
        if len(parts) >= 3 and parts[2] == "artifacts":
            stem = parts[3][:-3] if parts[3].endswith(".md") else parts[3]
            stage = ARTIFACT_STAGE.get(stem)
            return ("feature", parts[1], stage) if stage else None
    if rel.startswith("project/"):
        stem = Path(rel).stem
        stage = ARTIFACT_STAGE.get(stem)
        return ("project", None, stage) if stage else None
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    cwd = Path(payload.get("cwd") or os.getcwd())
    session_id = payload.get("session_id") or payload.get("conversation_id") or "default"
    try:
        active = context.active(cwd, session_id)
        stale = evidence.refresh_staleness(cwd, active["context_id"]) if active else []
        if stale:
            print(f"[flowguard] 代码/规格已变化，证据已过期: {', '.join(stale)}", file=sys.stderr)
    except Exception:
        active = None
    if payload.get("tool_name") == "Bash" and active:
        command = tool_input.get("command") or ""
        kind = _evidence_kind(command)
        exit_code = _exit_code(payload)
        if kind and exit_code is not None:
            command_hash = hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]
            try:
                rec = evidence.record(
                    cwd, active["context_id"], kind=kind, producer="hook:bash",
                    result="pass" if exit_code == 0 else "fail",
                    summary=f"受观察命令 exit_code={exit_code}",
                    source_ref=f"command-sha256:{command_hash}",
                )
                print(
                    f"[flowguard] 已记录证据 {rec['evidence_id']} ({kind}, {rec['result']})",
                    file=sys.stderr,
                )
            except Exception:
                pass
    info = _parse_artifact(file_path) if file_path else None
    if not info:
        return 0
    scope, fid, stage = info
    try:
        if scope == "feature":
            owner = state.load_feature(cwd, fid)
            jscope = f"feature:{fid}"
        else:
            owner = state.load_project(cwd)
            jscope = "project"
    except Exception:
        return 0

    degraded = state.degrade_from(owner, stage)
    if degraded:
        if scope == "feature":
            state.save_feature(cwd, owner)
        else:
            state.save_project(cwd, owner)
        journal.append(cwd, jscope, "artifact_rework_degrade",
                       {"artifact": Path(file_path).name, "degraded": degraded})
        print(f"[flowguard] 产物回改，已降级阶段: {', '.join(degraded)}", file=sys.stderr)

    # 完整性校验（WARNING 级提示，不阻断）
    try:
        text = Path(file_path).read_text(encoding="utf-8")
        issues = []
        if stage == "requirements" and fid:
            issues = validation.validate_requirements(text, fid)
        elif stage == "review" and fid:
            issues = validation.validate_review(text)
        for i in issues:
            if i["level"] in ("ERROR", "WARNING"):
                print(f"[flowguard] {i['level']}: {i['message']} → {i['fix']}", file=sys.stderr)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
