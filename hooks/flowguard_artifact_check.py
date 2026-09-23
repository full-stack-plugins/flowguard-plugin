#!/usr/bin/env python3
"""PostToolUse：证据采集与阶段文档失效提示（恒 exit 0）。"""
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import codereview_evidence, context, evidence, stage_docs, tool_scope  # noqa: E402

# artifact 文件名 → 阶段（用于降级与校验路由）
ARTIFACT_STAGE = {
    "01-requirements": "requirements", "02-architecture": "architecture",
    "03-solution": "solution", "04-testcases": "testcases",
    "05-hld": "hld", "06-lld": "lld", "07-standards": "standards",
    "08-review": "review", "09-docs": "docs", "10-release": "release",
}
CODEGUARD_MCP_TOOLS = ("mcp__codeguard__check_code_style", "mcp__codeguard__auto_fix")


def _codeguard_outcome(tool_name, tool_response, requested_languages):
    """仅从完整的 CodeGuard MCP 逐语言契约推导结果。"""
    if not isinstance(tool_response, dict) or tool_response.get("isError") is True:
        return "warning", "CodeGuard MCP 调用失败或缺少结构化回执"
    content = tool_response.get("content")
    if not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict):
        return "warning", "CodeGuard MCP 回执内容缺失或不唯一"
    block = content[0]
    if block.get("type") != "text" or not isinstance(block.get("text"), str):
        return "warning", "CodeGuard MCP 回执不是文本结果"
    try:
        data = json.loads(block["text"])
    except ValueError:
        return "warning", "CodeGuard MCP 回执无法解析"
    if tool_name == "mcp__codeguard__auto_fix":
        data = data.get("check") if isinstance(data, dict) else None
    if not isinstance(data, list) or not data:
        return "warning", "CodeGuard 未返回实际执行的检查项"
    if requested_languages is not None and (
        not isinstance(requested_languages, list)
        or not all(isinstance(item, str) and item for item in requested_languages)
    ):
        return "warning", "CodeGuard 请求的语言范围非法"
    seen = set()
    failed = 0
    unverified = 0
    for row in data:
        if not isinstance(row, dict):
            return "warning", "CodeGuard 检查项结构非法"
        language = row.get("language")
        if not isinstance(language, str) or not language or language in seen:
            return "warning", "CodeGuard 检查语言缺失或重复"
        seen.add(language)
        status = row.get("status")
        passed = row.get("passed")
        exit_code = row.get("exit_code")
        if type(passed) is not bool or type(exit_code) is not int:
            return "warning", "CodeGuard 检查项结果字段非法"
        if status == "PASS" and passed and exit_code == 0:
            continue
        if status == "FAIL" and not passed:
            failed += 1
        else:
            unverified += 1
    if requested_languages and seen != set(requested_languages):
        return "warning", "CodeGuard 返回的语言范围与请求不一致"
    if failed:
        return "fail", f"CodeGuard {len(data)} 项检查中 {failed} 项 FAIL"
    if unverified:
        return "warning", f"CodeGuard {len(data)} 项检查中 {unverified} 项未验证或不一致"
    return "pass", f"CodeGuard {len(data)} 项逐语言检查 PASS"

def _evidence_kind(command):
    """只对单条实际运行测试的命令记录观察证据；检查器需独立结构化回执。"""
    if not isinstance(command, str) or re.search(r"[;&|><`\n]|\$\(|\$\{", command):
        return None
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    if not words:
        return None
    program = Path(words[0]).name.lower()
    args = words[1:]
    if any(arg in ("--version", "-V", "--help", "-h", "--collect-only", "--no-run", "--dry-run")
           or arg.lower().startswith(("-dskiptests", "-dmaven.test.skip")) for arg in args):
        return None
    if program in ("python", "python3") and args[:2] in (["-m", "unittest"], ["-m", "pytest"]):
        return "tests"
    if program in ("pytest", "unittest"):
        return "tests"
    if program in ("mvn", "gradle", "npm", "pnpm", "cargo") and "test" in args:
        return "tests"
    return None


def _exit_code(payload):
    response = _tool_response(payload)
    if isinstance(response, dict) and type(response.get("exit_code")) is int:
        return response["exit_code"]
    return None


def _tool_response(payload):
    """Codex/ZCode 与 Kimi 的 PostToolUse 结果字段；不推测缺失的退出码。"""
    for key in ("tool_response", "tool_result", "tool_output"):
        if key in payload:
            return payload[key]
    return None


def _test_outcome(command, exit_code, tool_response):
    if exit_code != 0:
        return "fail", f"受观察测试命令 exit_code={exit_code}"
    if not isinstance(tool_response, dict):
        return "warning", "测试命令未返回可核对的执行摘要"
    output = "\n".join(
        tool_response[key] for key in ("output", "stdout", "stderr")
        if isinstance(tool_response.get(key), str)
    )
    words = shlex.split(command)
    program = Path(words[0]).name.lower()
    if ((program in ("python", "python3") and words[1:3] == ["-m", "unittest"])
            or program == "unittest"):
        match = re.search(r"(?m)^Ran (\d+) tests? in [^\n]+$", output)
        skipped = re.search(r"(?m)^OK \(skipped=(\d+)\)$", output)
        if (match and int(match.group(1)) > (int(skipped.group(1)) if skipped else 0)
                and re.search(r"(?m)^OK(?: \([^\n]*\))?$", output)):
            return "pass", f"受观察测试命令完成 {match.group(1)} 个用例"
    elif program in ("python", "python3", "pytest") and (program == "pytest" or words[1:3] == ["-m", "pytest"]):
        match = re.search(r"(?m)^=+[^\n]*\b([1-9]\d*) passed\b[^\n]*=+$|^([1-9]\d*) passed\b[^\n]*$", output)
        if match and not re.search(r"\b[1-9]\d* (?:failed|error|errors)\b", match.group(0)):
            return "pass", "受观察测试命令有非零通过用例"
    elif program == "mvn":
        rows = re.findall(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)", output)
        if rows and sum(int(run) - int(skipped) for run, _, _, skipped in rows) > 0 and all(
            int(failed) == int(errors) == 0 for _, failed, errors, _ in rows
        ):
            return "pass", "受观察 Maven 测试有非零执行用例"
    elif program == "gradle":
        rows = re.findall(r"(?m)^(\d+) tests? completed, (\d+) failed(?:, (\d+) skipped)?\b", output)
        if rows and sum(int(run) - int(skipped or 0) for run, _, skipped in rows) > 0 and all(
            int(failed) == 0 for _, failed, _ in rows
        ):
            return "pass", "受观察 Gradle 测试有非零执行用例"
    elif program == "cargo":
        rows = re.findall(r"test result: ok\. (\d+) passed; (\d+) failed", output)
        if rows and sum(int(passed) for passed, _ in rows) > 0 and all(int(failed) == 0 for _, failed in rows):
            return "pass", "受观察 Cargo 测试有非零通过用例"
    elif program in ("npm", "pnpm"):
        match = re.search(r"(?m)^[ \t]*Tests[ \t]*:?[ \t]*([1-9]\d*) passed\b", output)
        if match and not re.search(r"\b[1-9]\d* failed\b", output):
            return "pass", "受观察 JavaScript 测试有非零通过用例"
    return "warning", "测试命令 exit_code=0，但无法确认执行了非零测试"


def _parse_artifact(path):
    """返回 (scope, feature_id|None, stage) 或 None。"""
    p = str(path).replace("\\", "/")
    if "/docs/" in p:
        rel = p.rsplit("/docs/", 1)[1]
    elif p.startswith("docs/"):
        rel = p[5:]
    else:
        rel = None
    if rel and rel.endswith(".md"):
        parts = rel.split("/")
        if len(parts) == 3 and parts[0] == "features":
            stage = ARTIFACT_STAGE.get(Path(parts[2]).stem)
            return ("docs_feature", parts[1], stage) if stage else None
        if len(parts) == 2 and parts[0] == "project":
            stage = ARTIFACT_STAGE.get(Path(parts[1]).stem)
            return ("docs_project", None, stage) if stage else None
    return None


def _touched_paths(tool_name, tool_input):
    if tool_name == "apply_patch":
        command = tool_input.get("command")
        if not isinstance(command, str):
            return []
        return [match.group(1).strip() for match in re.finditer(
            r"^\*\*\* (?:Add File|Update File|Delete File|Move to):\s*(.+)$",
            command, flags=re.MULTILINE,
        )]
    file_path = tool_input.get("file_path")
    return [file_path] if isinstance(file_path, str) and file_path else []


def _emit(notices):
    if notices:
        print(json.dumps({"systemMessage": "\n".join(notices)}, ensure_ascii=False))
    else:
        print("{}")


def _notice(notices, message):
    notices.append(message)
    print(message, file=sys.stderr)


def _check_artifact(cwd, file_path, active, notices):
    info = _parse_artifact(file_path)
    if not info:
        return
    _scope, fid, stage = info
    task_id = fid or (active or {}).get("task_id") or "project"
    try:
        phase = stage_docs.read(cwd, task_id, next(
            aid for aid, item in stage_docs.registry.ARTIFACTS.items() if item["stage"] == stage
        ))
        if phase["status"] == "invalidated":
            _notice(notices, f"[flowguard] 阶段文档已失效: {phase['path']}；请复核后重新申请验收")
    except Exception as error:
        _notice(notices, f"[flowguard] 阶段文档待修复: {error}")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        _emit([])
        return 0
    if not isinstance(payload, dict):
        _emit([])
        return 0
    notices = []
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    cwd = Path(payload.get("cwd") or os.getcwd())
    session_id = payload.get("session_id") or payload.get("conversation_id") or "default"
    try:
        active = context.active(cwd, session_id)
        stale = evidence.refresh_staleness(cwd, active["context_id"]) if active else []
        if stale:
            _notice(notices, f"[flowguard] 代码/规格已变化，证据已过期: {', '.join(stale)}")
    except Exception:
        active = None
    if payload.get("tool_name") in ("Bash", "Shell") and active:
        command = tool_input.get("command") or ""
        kind = _evidence_kind(command)
        exit_code = _exit_code(payload)
        if kind:
            command_hash = hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]
            response = _tool_response(payload)
            if payload.get("hook_event_name") == "PostToolUseFailure":
                result, summary = "fail", "受观察测试工具执行失败（宿主未提供退出码）"
            elif exit_code is None:
                result, summary = "warning", "测试工具回执缺少明确整数退出码"
            else:
                result, summary = _test_outcome(command, exit_code, response)
            try:
                rec = evidence.record(
                    cwd, active["context_id"], kind=kind, producer="hook:bash",
                    result=result, summary=summary,
                    source_ref=f"command-sha256:{command_hash}",
                )
                _notice(notices, f"[flowguard] 已记录证据 {rec['evidence_id']} ({kind}, {rec['result']})")
            except Exception:
                pass
        if codereview_evidence.is_evidence_command(command):
            response = _tool_response(payload)
            output = response.get("output") if isinstance(response, dict) else None
            result, summary = codereview_evidence.classify(cwd, session_id, exit_code, output)
            if result is None:
                _notice(notices, f"[flowguard] {summary}，未登记当前任务证据")
            else:
                output_hash = hashlib.sha256((output or "").encode("utf-8")).hexdigest()[:16]
                try:
                    rec = evidence.record(
                        cwd, active["context_id"], kind="semantic_review",
                        producer="hook:codereview-cli", result=result, summary=summary,
                        source_ref=f"codereview-output-sha256:{output_hash}",
                    )
                    _notice(notices, f"[flowguard] 已记录 CodeReview 证据 {rec['evidence_id']} ({result})")
                except Exception as error:
                    _notice(notices, f"[flowguard] CodeReview 证据登记失败: {error}")
    tool_name = payload.get("tool_name")
    if tool_name in CODEGUARD_MCP_TOOLS and active:
        if not tool_scope.same_git_worktree(cwd, tool_input.get("path")):
            _notice(notices, "[flowguard] CodeGuard MCP 目标不是当前 worktree，未登记证据")
        else:
            response = _tool_response(payload)
            result, summary = _codeguard_outcome(
                tool_name, response, tool_input.get("languages"),
            )
            response_hash = hashlib.sha256(json.dumps(
                response, ensure_ascii=False, sort_keys=True,
            ).encode("utf-8")).hexdigest()[:16]
            try:
                rec = evidence.record(
                    cwd, active["context_id"], kind="static_analysis",
                    producer="hook:codeguard-mcp", result=result, summary=summary,
                    source_ref=f"mcp-response-sha256:{response_hash}",
                )
                _notice(notices, f"[flowguard] 已记录 CodeGuard 证据 {rec['evidence_id']} ({result})")
            except Exception as error:
                _notice(notices, f"[flowguard] CodeGuard 证据登记失败: {error}")
    for file_path in _touched_paths(payload.get("tool_name"), tool_input):
        _check_artifact(cwd, file_path, active, notices)
    _emit(notices)
    return 0


if __name__ == "__main__":
    sys.exit(main())
