"""新治理模型的确定性策略引擎。"""
from pathlib import Path

from . import context, discovery, evidence

ACTIONS = ("read", "spec_write", "test_write", "code_write", "git_commit", "release")
COMMIT_EVIDENCE = ("tests", "static_analysis", "semantic_review")
RELEASE_EVIDENCE = ("release_readiness", "user_acceptance")


def _deny(code, message, fix, *, allowed_actions=None, missing=None):
    return {
        "allowed": False,
        "envelope": {
            "severity": "ERROR",
            "code": code,
            "message": message,
            "fix": fix,
            "allowed_actions": list(allowed_actions or ["read", "spec_write"]),
            "missing": list(missing or []),
        },
    }


def _allow(ctx=None):
    return {"allowed": True, "envelope": None, "context": ctx}


def _spec_ref_valid(root, ctx):
    ref = ctx.get("spec_ref")
    if not ref:
        return False
    if ref.startswith(("http://", "https://")):
        return ctx.get("spec_system") == "external"
    return (Path(root) / ref).exists()


def evaluate(root, action, *, session_id, path=None):
    if action not in ACTIONS:
        raise ValueError(f"未知治理动作: {action}")
    if action in ("read", "spec_write"):
        return _allow()

    snapshot = discovery.discover(root)
    if not snapshot["git"]["is_repository"]:
        return _allow()
    ctx = context.active(root, session_id)
    if not ctx or ctx.get("status") != "active":
        return _deny(
            "governance_context_required",
            "Git 项目尚未绑定本会话的任务上下文",
            "先运行 discover，分类任务后用 context bind 绑定原生规格；读取、补规格和请求批准仍允许",
            allowed_actions=["read", "spec_write"],
            missing=["task_context"],
        )
    task_type = ctx.get("task_type")
    if task_type == "read_only":
        return _deny(
            "governance_read_only_context", "当前上下文声明为只读分析，不能修改业务代码",
            "若任务范围已改变，重新分类并绑定上下文", missing=["writable_task_type"],
        )
    if action == "test_write":
        return _allow(ctx)
    if task_type == "important_change":
        if ctx.get("spec_system") in (None, "none") or not _spec_ref_valid(root, ctx):
            return _deny(
                "governance_spec_required", "重要变更缺少有效的原生规格引用",
                "选择 Spec Kit/OpenSpec/Superpowers 事实源，必要时先取得初始化批准，再重新绑定",
                missing=["spec_ref"],
            )
        if "scope_approved" not in (ctx.get("approvals") or {}):
            return _deny(
                "governance_approval_required", "重要变更尚无明确的范围批准",
                "向用户展示目标、非目标、验收标准和文件影响；用户确认后记录 scope_approved",
                missing=["scope_approved"],
            )

    if action == "code_write":
        return _allow(ctx)

    relation_blockers = context.blockers(root, ctx["context_id"])
    if action == "release" and relation_blockers:
        return _deny(
            "governance_dependencies_incomplete", "仍有未完成的依赖或必要子任务",
            "先完成列出的依赖/子任务并补父级集成验证",
            missing=relation_blockers,
        )

    valid = evidence.valid_kinds(root, ctx["context_id"])
    required = list(COMMIT_EVIDENCE)
    required.extend(ctx.get("required_evidence") or [])
    if action == "release":
        required.extend(RELEASE_EVIDENCE)
    missing = [kind for kind in dict.fromkeys(required) if kind not in valid]
    if missing:
        return _deny(
            "governance_evidence_required", "当前代码指纹缺少有效证据: " + ", ".join(missing),
            "执行对应检查并用 evidence record 记录真实结果；代码变化后需重新生成过期证据",
            allowed_actions=["read", "spec_write", "test_write", "code_write"],
            missing=missing,
        )
    return _allow(ctx)
