"""消费 CodeReview v1 的只读证据回执，不把 advisory 当成放行。"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import subprocess

from . import discovery

SCOPE_FIELDS = {
    "repo", "worktree", "common_dir", "endpoint", "model",
    "context_policy", "config_digest", "execution_mode",
}
RESULT_STATES = {"success", "partial", "failed", "skipped", "cancelled"}


def _valid_finding(value):
    if not isinstance(value, dict):
        return False
    path = value.get("path")
    if (not isinstance(path, str) or not path
            or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts
            or "\\" in path):
        return False
    start, end = value.get("start_line"), value.get("end_line")
    return (isinstance(value.get("content"), str) and bool(value["content"])
            and type(start) is int and type(end) is int and 1 <= start <= end
            and isinstance(value.get("severity"), str) and bool(value["severity"])
            and isinstance(value.get("category"), str) and bool(value["category"]))


def is_evidence_command(command):
    """只认单条 CodeReview CLI evidence 命令；其它 Shell 文本不冒充回执。"""
    if not isinstance(command, str) or any(token in command for token in (";", "&", "|", "<", ">", "`", "\n", "$(")):
        return False
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if len(words) < 3 or Path(words[0]).name not in ("python", "python3"):
        return False
    if Path(words[1]).name != "codereview.py" or words[2] != "evidence":
        return False
    return len(words) == 3 or (len(words) == 5 and words[3] == "--request" and bool(words[4]))


def _git(root, *args, optional=False):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-C", str(root), *args],
        capture_output=True, env=env, check=False, timeout=20,
    )
    if result.returncode:
        if optional:
            return None
        raise ValueError("无法读取当前 Git 暂存区")
    return result.stdout


def _current_candidate(root):
    """与 CodeReview v1 一致：SHA-256([HEAD, 排序后的索引 mode/oid/path])。"""
    root = Path(root).resolve()
    head_raw = _git(root, "rev-parse", "--verify", "HEAD", optional=True)
    head = head_raw.decode("ascii").strip() if head_raw else None
    entries = []
    for line in _git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not line:
            continue
        try:
            metadata, raw_path = line.split(b"\t", 1)
            mode, oid, stage = metadata.decode("ascii").split()
            path = os.fsdecode(raw_path)
        except (ValueError, UnicodeError) as error:
            raise ValueError("暂存区条目非法") from error
        parts = PurePosixPath(path).parts
        if (mode not in ("100644", "100755") or stage != "0" or not parts
                or PurePosixPath(path).is_absolute() or ".." in parts
                or "\\" in path or any(part.lower() == ".git" for part in parts)):
            raise ValueError("暂存区条目不安全或未合并")
        entries.append((mode, oid, path))
    entries.sort(key=lambda item: os.fsencode(item[2]))
    encoded = json.dumps([head, entries], sort_keys=True, ensure_ascii=True).encode("utf-8")
    if head is None:
        changed = {path for _, _, path in entries}
    else:
        changed = {
            os.fsdecode(path) for path in _git(
                root, "diff", "--cached", "--no-ext-diff", "--no-textconv",
                "--name-only", "-z", "HEAD", "--",
            ).split(b"\0") if path
        }
    return head, hashlib.sha256(encoded).hexdigest(), changed


def classify(root, session_id, exit_code, output):
    """返回 (结果, 摘要)；跨 worktree 返回 (None, 原因)。"""
    if type(exit_code) is not int or exit_code != 0 or not isinstance(output, str):
        return "warning", "CodeReview evidence 命令未成功返回结构化回执"
    try:
        value = json.loads(output)
    except ValueError:
        return "warning", "CodeReview evidence 回执无法解析"
    if not isinstance(value, dict) or value.get("version") != 1 or value.get("producer") != "codereview-plugin":
        return "warning", "CodeReview evidence 协议版本或生产者非法"
    scope = value.get("scope")
    if not isinstance(scope, dict) or set(scope) != SCOPE_FIELDS:
        return "warning", "CodeReview evidence 作用域非法"
    snapshot = discovery.discover(root)
    if (scope.get("worktree") != snapshot["git"]["root"]
            or scope.get("common_dir") != snapshot["git"]["common_dir"]
            or scope.get("repo") != snapshot["git"]["common_dir"]):
        return None, "CodeReview evidence 属于其他 Git worktree"
    if (value.get("host") not in ("codex", "zcode", "kimi")
            or value.get("session") != session_id
            or not isinstance(value.get("task_id"), str) or not value["task_id"]):
        return "warning", "CodeReview evidence 宿主、会话或任务标识不匹配"
    try:
        head, current, changed = _current_candidate(root)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return "warning", "无法核对 CodeReview 当前暂存区指纹"
    if value.get("fingerprint") != current or value.get("baseline") != head:
        return "warning", "CodeReview evidence 暂存区指纹或基线已过期"
    if not changed:
        return "warning", "CodeReview 当前暂存区无实际变更"
    report = value.get("report")
    if report is None:
        return "warning", "CodeReview 尚无审查报告"
    if not isinstance(report, dict) or report.get("execution_status") not in RESULT_STATES:
        return "warning", "CodeReview 审查报告状态非法"
    if (report.get("stale") or report.get("fingerprint") != current
            or report.get("baseline") != head or report.get("scope") != scope):
        return "warning", "CodeReview 审查报告与当前暂存区不匹配"
    findings = report.get("findings")
    if not isinstance(findings, list) or not isinstance(report.get("warnings"), list):
        return "warning", "CodeReview 审查问题或警告列表非法"
    if any(not _valid_finding(item) for item in findings):
        return "warning", "CodeReview 问题缺少可定位的代码证据"
    if any(item["path"] not in changed for item in findings):
        return "warning", "CodeReview 问题未指向当前暂存改动"
    if report["execution_status"] != "success" or report.get("coverage_status") != "limited":
        return "warning", "CodeReview 审查尚未形成有效完整回执"
    if (type(report.get("files_reviewed")) is not int or report["files_reviewed"] <= 0
            or report["files_reviewed"] > len(changed)):
        return "warning", "CodeReview 未证明审查过文件"
    if findings:
        return "fail", f"CodeReview 报告 {len(findings)} 项待处理问题"
    return "warning", "CodeReview 已完成建议性审查；有限覆盖且无自动放行结论"
