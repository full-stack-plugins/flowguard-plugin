#!/usr/bin/env python3
"""PreToolUse：按治理上下文校验写码、提交与发布；旧状态仅作兼容。"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flowguard_lib import discovery, governance, registry, tool_scope  # noqa: E402

CODEGUARD_MCP_ACTIONS = {
    "mcp__codeguard__list_languages": "read",
    "mcp__codeguard__analyze_java_impact": "read",
    "mcp__codeguard__check_code_style": "test_write",
    "mcp__codeguard__auto_fix": "code_write",
}
RELEASE_VERBS = {
    "mvn": ("deploy", "release"), "mvnw": ("deploy", "release"),
    "gradle": ("publish", "release"), "gradlew": ("publish", "release"),
    "npm": ("publish",), "yarn": ("publish",), "pnpm": ("publish",),
    "cargo": ("publish",), "docker": ("push",), "helm": ("push",),
    "twine": ("upload",), "make": ("release",),
}
RELEASE_TARGET_FLAGS = (
    "--prefix", "--workspace", "--dir", "--cwd", "--manifest-path",
    "--project-dir", "--build-file", "--file", "--directory", "--projects",
    "--repo", "-R", "-C", "-w", "-p", "-b", "-f", "-pl",
)
GIT_HISTORY_MUTATORS = {
    "merge", "cherry-pick", "revert", "rebase", "am",
    "commit-tree", "update-ref", "reset", "filter-branch",
}


def _relative(cwd, path):
    if not path:
        return ""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    try:
        candidate = candidate.resolve()
    except (OSError, RuntimeError):
        return "/<unresolved-write-target>"
    try:
        candidate = candidate.relative_to(Path(cwd).resolve())
    except ValueError:
        pass
    return str(candidate).replace("\\", "/")


def _write_target_in_root(cwd, path, root):
    try:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        candidate.resolve().relative_to(Path(root).resolve())
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _write_action(cwd, path):
    rel = _relative(cwd, path)
    if rel.startswith((".specify/", "openspec/", "docs/")):
        return "spec_write"
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


def _patch_paths(command):
    if not isinstance(command, str) or not command.startswith("*** Begin Patch"):
        return []
    return [match.group(1).strip() for match in re.finditer(
        r"^\*\*\* (?:Add File|Update File|Delete File|Move to):\s*(.+)$",
        command, flags=re.MULTILINE,
    )]


def _print_denial(env):
    print(f"ERROR: {env['message']}", file=sys.stderr)
    print(f"Fix: {env['fix']}", file=sys.stderr)
    if env.get("missing"):
        print(f"Missing: {', '.join(env['missing'])}", file=sys.stderr)
    if env.get("allowed_actions"):
        print(f"Allowed: {', '.join(env['allowed_actions'])}", file=sys.stderr)
    print(f"[flowguard] code={env['code']}", file=sys.stderr)


def _is_git_commit(command):
    try:
        words = shlex.split(command)
    except ValueError:
        words = []
    if words and Path(words[0]).name.lower() == "git" and "commit" in words[1:]:
        return True
    pattern = (
        r"(?:^|[\s;&|('\\\"])"
        r"(?:command\s+)?(?:\S+/)?git"
        r"(?:\s+(?:(?:-C|-c|--git-dir|--work-tree)\s+\S+|(?:-c|--git-dir|--work-tree)=\S+))*"
        r"\s+commit\b"
    )
    return bool(re.search(pattern, command, re.IGNORECASE))


def _is_git_history_mutation(command, cwd):
    """拒绝可能隐式生成提交或移动引用的直接 Git 子命令。"""
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    return (bool(words) and Path(words[0]).name.lower() == "git"
            and _direct_git_commit_target(command, cwd) is None
            and any(word in GIT_HISTORY_MUTATORS for word in words[1:]))


def _direct_git_commit_target(command, cwd):
    """只给可解析的单条直接 git commit 求目标目录；包装器/配置覆盖保持未知。"""
    try:
        words = shlex.split(command)
        if not words or Path(words[0]).name.lower() != "git":
            return None
        target = Path(cwd).resolve()
        index = 1
        while index < len(words):
            word = words[index]
            if word == "commit":
                return target
            if word == "-C" and index + 1 < len(words):
                target = (target / words[index + 1]).resolve()
                index += 2
            elif word.startswith("-C") and len(word) > 2:
                target = (target / word[2:]).resolve()
                index += 1
            elif word in ("--no-pager", "--paginate", "--no-optional-locks"):
                index += 1
            else:
                return None
    except (OSError, ValueError):
        return None
    return None


def _has_shell_operators(command):
    """识别复合执行，避免 commit 的较弱门禁掩盖同一 Shell 中的发布。"""
    if re.search(r"[`\n]|\$\(", command):
        return True
    try:
        words = shlex.split(command)
        if words and Path(words[0]).name.lower() in ("sh", "bash", "zsh", "dash"):
            return True  # 包装脚本的内部动作和目标无法逐项核验
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return any(token and set(token) <= set(";&|<>") for token in lexer)
    except ValueError:
        return True


def _release_words(command):
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    if not words:
        return None
    program = Path(words[0]).name.lower()
    if program == "gh" and "release" in words[1:] and any(
        word in ("create", "upload") for word in words[1:]
    ):
        return words
    return words if any(word in RELEASE_VERBS.get(program, ()) for word in words[1:]) else None


def _release_target_unverified(command):
    words = _release_words(command)
    if not words:
        return True
    for word in words[1:]:
        if word in RELEASE_TARGET_FLAGS:
            return True
        if any(word.startswith(flag + "=") for flag in RELEASE_TARGET_FLAGS if flag.startswith("--")):
            return True
        if any(word.startswith(flag) and len(word) > len(flag)
               for flag in ("-R", "-C", "-w", "-p", "-b", "-f", "-pl")):
            return True
    return False


def _is_bundled_flowguard_cli(words, cwd):
    if len(words) < 2:
        return False
    script = words[1]
    if script == "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py":
        return True
    return (Path(cwd) / script).resolve() == (ROOT / "scripts" / "flowguard_state.py").resolve()


def _bash_action(command, cwd):
    """无法证明是单条只读/补救命令的 Shell，一律当作潜在写码动作。"""
    if _is_git_history_mutation(command, cwd):
        return "git_history_mutation"
    is_commit = _direct_git_commit_target(command, cwd) is not None or _is_git_commit(command)
    is_release = bool(_release_words(command)) or any(
        pattern in command.lower() for pattern in registry.RELEASE_CMD_PATTERNS
    )
    if (is_commit or is_release) and _has_shell_operators(command):
        return "compound_command"
    if is_commit:
        return "git_commit"
    if is_release:
        return "release"
    scan = command.replace("${CLAUDE_PLUGIN_ROOT}", "PLUGIN_ROOT")
    if re.search(r"[;&|><`\n]|\$\(|\$\{", scan):
        return "code_write"
    try:
        words = shlex.split(command)
    except ValueError:
        return "code_write"
    if not words:
        return None
    command_name = Path(words[0]).name.lower()
    if command_name == "rg" and any(word == "--pre" or word.startswith("--pre=") for word in words[1:]):
        return "code_write"
    if command_name in ("pwd", "ls", "cat", "head", "tail", "rg", "grep", "wc"):
        return None
    if command_name == "git" and len(words) > 1:
        if any(word in ("--ext-diff", "--textconv", "--output") or word.startswith("--output=")
               for word in words[2:]):
            return "code_write"
        if words[1] in ("status", "diff", "show", "log", "rev-parse", "ls-files", "ls-remote"):
            return None
        if words[1] == "branch" and len(words) > 2 and words[2] in ("--show-current", "--list", "-a", "-r"):
            return None
        if words[1] in ("add", "apply", "mv"):
            return "code_write"
        return "unclassified"
    if command_name in ("openspec", "specify"):
        return "spec_write"
    if command_name in ("python", "python3") and _is_bundled_flowguard_cli(words, cwd):
        return "spec_write"
    if command_name in ("pytest", "unittest"):
        return "test_write"
    if command_name in ("python", "python3") and words[1:3] == ["-m", "unittest"]:
        return "test_write"
    if command_name in ("mvn", "gradle", "cargo", "npm") and "test" in words[1:]:
        return "test_write"
    return "code_write"


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("WARNING: flowguard_gate 收到非法 stdin，放行", file=sys.stderr)
        return 0
    if not isinstance(payload, dict):
        print("WARNING: flowguard_gate 收到非对象 stdin，放行", file=sys.stderr)
        return 0
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    cwd = payload.get("cwd") or os.getcwd()

    session_id = payload.get("session_id") or payload.get("conversation_id") or "default"
    action, path = None, None
    command = None
    write_targets = []
    if tool == "apply_patch":
        paths = _patch_paths(tool_input.get("command"))
        write_targets = paths
        actions = {_write_action(cwd, item) for item in paths} if paths else {"code_write"}
        action = next(item for item in ("code_write", "test_write", "spec_write") if item in actions)
    elif tool in ("Write", "Edit", "MultiEdit", "WriteFile", "StrReplaceFile"):
        path = tool_input.get("file_path")
        write_targets = [path] if isinstance(path, str) and path else []
        action = _write_action(cwd, path) if isinstance(path, str) and path else "code_write"
    elif tool in ("Bash", "Shell"):
        command = tool_input.get("command")
        action = _bash_action(command, cwd) if isinstance(command, str) and command else "code_write"
        if action is None:
            return 0
    elif tool in ("Read", "ReadFile", "ReadMediaFile", "Glob", "Grep", "LS",
                  "ToolSearch", "TodoWrite", "SetTodoList", "update_plan"):
        return 0
    elif tool in CODEGUARD_MCP_ACTIONS:
        action = CODEGUARD_MCP_ACTIONS[tool]
        if action == "read":
            return 0
    else:
        action = "unclassified"

    if action == "compound_command":
        _print_denial({
            "code": "governance_compound_command",
            "message": "包含提交或发布的复合或包装 Shell 命令无法逐动作核验",
            "fix": "把 Git 提交、发布和其它 Shell 操作拆成独立直接工具调用，分别通过对应门禁",
            "allowed_actions": ["read", "spec_write", "test_write"],
        })
        return 2
    if action == "git_history_mutation":
        _print_denial({
            "code": "governance_git_history_mutation_unverified",
            "message": "该 Git 命令可能直接生成提交或改写引用，无法经过逐次提交审查",
            "fix": "先取得用户对历史操作的明确授权；将可审查的改动留在工作树，完成检查后再单独执行 git commit",
            "allowed_actions": ["read", "spec_write", "test_write", "code_write"],
        })
        return 2
    if action == "release" and _release_target_unverified(command):
        _print_denial({
            "code": "governance_release_target_unverified",
            "message": "发布命令的项目目标无法确认属于当前 worktree",
            "fix": "进入目标 worktree 后使用单条直接发布命令；不要通过 --prefix、--workspace 或项目路径选项切换发布目标",
            "allowed_actions": ["read", "spec_write", "test_write"],
        })
        return 2
    commit_target = _direct_git_commit_target(command, cwd) if action == "git_commit" else None

    try:
        snapshot = discovery.discover(Path(cwd))
        if snapshot["git"]["is_repository"]:
            if any(not _write_target_in_root(cwd, target, snapshot["git"]["root"])
                   for target in write_targets):
                res = {"allowed": False, "envelope": {
                    "code": "governance_write_target_mismatch",
                    "message": "文件写入目标不属于当前会话绑定的 Git worktree",
                    "fix": "进入目标 worktree 并重新绑定任务；不要使用路径穿越或指向仓库外的符号链接",
                    "allowed_actions": ["read", "spec_write", "test_write"],
                }}
            elif action == "git_commit" and not tool_scope.same_git_worktree(
                cwd, str(commit_target) if commit_target else None,
                expected_root=snapshot["git"]["root"],
            ):
                res = {"allowed": False, "envelope": {
                    "code": "governance_git_target_mismatch",
                    "message": "无法证明 Git 提交目标属于当前会话绑定的 worktree",
                    "fix": "切换到目标 worktree 重新绑定上下文，并使用单条直接 git commit 命令；勿使用 Shell 包装器或改写 Git 目录的全局选项",
                    "allowed_actions": ["read", "spec_write", "test_write"],
                }}
            elif tool in CODEGUARD_MCP_ACTIONS and not tool_scope.same_git_worktree(
                cwd, tool_input.get("path"), expected_root=snapshot["git"]["root"],
            ):
                res = {"allowed": False, "envelope": {
                    "code": "governance_tool_scope_required",
                    "message": "CodeGuard MCP 的检查或修复目标未明确绑定到当前 Git worktree",
                    "fix": "显式传入当前项目或其子路径作为 path；跨 worktree 任务需在目标 worktree 重新绑定上下文",
                    "allowed_actions": ["read", "spec_write", "test_write"],
                }}
            elif action == "unclassified":
                git_command = bool(command and re.match(r"^(?:\S+/)?git\s", command))
                res = {"allowed": False, "envelope": {
                    "code": "governance_unclassified_tool",
                    "message": ("无法判定该 Git 命令是否会修改历史或发布"
                                if git_command else f"无法判定工具 {tool!r} 是否会修改项目或执行提交/发布"),
                    "fix": ("改用已识别的 Git 只读或暂存命令；其他 Git 操作需先新增风险分类与回归测试"
                            if git_command else "改用已识别的只读、规格、测试或 Shell 工具；新工具需先新增风险分类和回归测试"),
                    "allowed_actions": ["read", "spec_write", "test_write"],
                }}
            else:
                res = governance.evaluate(Path(cwd), action, session_id=session_id, path=path)
        elif action == "git_commit" and (
            commit_target is None or discovery.discover(commit_target)["git"]["is_repository"]
        ):
            _print_denial({
                "code": "governance_git_target_mismatch",
                "message": "当前目录不是 Git 项目，但提交命令可能指向其它 Git worktree",
                "fix": "进入目标 worktree，执行 SDD 发现与任务绑定后再提交",
            })
            return 2
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
