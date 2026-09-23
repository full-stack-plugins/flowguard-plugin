#!/usr/bin/env python3
"""flowguard 编排核 CLI（唯一判定源的对外命令面）。

退出码：0 成功；2 门禁拒绝；3 用法/状态错误。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flowguard_lib import (  # noqa: E402
    context, discovery, evidence, governance, registry,
    stage_docs, state, validation,
)
from flowguard_lib.diag import emit as emit_diag, envelope as mk_env  # noqa: E402


class Parser(argparse.ArgumentParser):
    """用法错误退出 3（默认 2 与门禁拒绝冲突）。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        emit_diag(mk_env("ERROR", "usage", message, "查看 --help"),
                  as_json="--json" in sys.argv)
        sys.exit(3)


_AS_JSON = False  # main() 从 args.json 设置：错误信封与正常输出同面


def _die(env, code=3, as_json=None):
    emit_diag(env, as_json=_AS_JSON if as_json is None else as_json)
    sys.exit(code)


def _out(data, as_json):
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif isinstance(data, dict) and any(isinstance(v, (list, dict)) for v in data.values()):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("; ".join(f"{k}={v}" for k, v in data.items()))


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def cmd_init(args):
    root = Path.cwd()
    created = stage_docs.ensure_project(root)
    _out({"initialized": True, "root": str(root), "created": created}, args.json)


def cmd_discover(args):
    """只读发现 Git、原生 SDD 标识、CLI 可用性和冲突。"""
    _out(discovery.discover(Path.cwd()), args.json)


def cmd_context(args):
    root = Path.cwd()
    if args.action == "bind":
        data = context.bind(
            root,
            session_id=args.session,
            task_id=args.task_id,
            task_type=args.task_type,
            spec_system=args.spec_system,
            spec_ref=args.spec_ref,
            parent_id=args.parent_id,
            depends_on=args.depends_on,
            required_evidence=args.require_evidence,
        )
    elif args.action == "show":
        data = context.load(root, args.context_id) if args.context_id else context.active(root, args.session)
        if data is None:
            _die(mk_env("ERROR", "context_not_bound", "当前会话没有 active 上下文",
                        "先运行 context bind"))
    elif args.action == "list":
        data = {"contexts": context.list_all(root)}
    elif args.action == "approve":
        data = context.approve(root, args.context_id, args.approval, actor=args.actor)
    elif args.action == "complete":
        data = context.complete(root, args.context_id)
    else:  # argparse choices 已防守；保留显式分支避免静默
        _die(mk_env("ERROR", "usage", f"未知 context action: {args.action}", "查看 context --help"))
    _out(data, args.json)


def cmd_evidence(args):
    root = Path.cwd()
    if args.action == "record":
        data = evidence.record(
            root, args.context_id, kind=args.kind, producer=args.producer,
            result=args.result, summary=args.summary, source_ref=args.source_ref,
            expires_on_change=args.expires_on_change,
        )
    elif args.action == "list":
        data = {
            "context_id": args.context_id,
            "valid_kinds": sorted(evidence.valid_kinds(root, args.context_id)),
            "evidence": evidence.list_all(root, args.context_id),
        }
    else:
        _die(mk_env("ERROR", "usage", f"未知 evidence action: {args.action}", "查看 evidence --help"))
    _out(data, args.json)


def cmd_governance(args):
    result = governance.evaluate(
        Path.cwd(), args.action, session_id=args.session, path=args.path,
    )
    if result["allowed"]:
        _out({
            "allowed": True,
            "action": args.action,
            "context_id": (result.get("context") or {}).get("context_id"),
        }, args.json)
        return
    _die(result["envelope"], code=2, as_json=args.json)


def cmd_stage(args):
    root = Path.cwd()
    if args.action == "status":
        data = stage_docs.snapshot(root, args.task_id)
    else:
        data = stage_docs.advance(
            root, args.task_id, args.stage, args.status,
            approval_ref=args.approval_ref, reason=args.reason,
        )
    _out(data, args.json)


def cmd_validate(args):
    """产物内容校验（REQ/追溯/结论）+ 下一阶段 Tier2 安装检查；范围 docs/features/<task-id>/。"""
    root = Path.cwd()
    tasks = stage_docs.recoverable(root)["tasks"]
    if args.task_id:
        tasks = [t for t in tasks if t.get("task_id") == args.task_id]
        if not tasks:
            _die(mk_env("ERROR", "unknown_task", f"功能文档不存在: {args.task_id}",
                        "先用 context bind 创建 docs/features/<task-id>/"), as_json=args.json)
    issues = []
    for task in tasks:
        task_id = task["task_id"]
        if task.get("error"):
            issues.append({"level": "ERROR", "path": f"docs/features/{task_id}",
                           "message": task["error"], "fix": "修复阶段文档元信息表"})
            continue
        req_text = _read(stage_docs.path_for(root, task_id, "01-requirements"))
        reqs = validation.requirement_ids(req_text)
        issues += validation.validate_requirements(req_text, task_id)
        issues += validation.validate_testcases(
            _read(stage_docs.path_for(root, task_id, "04-testcases")), reqs, root=root)
        issues += validation.validate_review(
            _read(stage_docs.path_for(root, task_id, "08-review")))
        next_stage = task.get("next_stage")
        if next_stage:
            stage = registry.ARTIFACTS[next_stage]["stage"]
            issues += validation.missing_tier2(
                [(skill, pkg, registry.install_cmd(skill, pkg))
                 for skill, pkg in registry.TIER2_REFS.get(stage, [])], root=root)
    has_error = any(i["level"] == "ERROR" for i in issues)
    if args.json:
        print(json.dumps({"issues": issues, "ok": not has_error}, ensure_ascii=False, indent=2))
    else:
        for i in issues:
            print(f"{i['level']}: [{i['path']}] {i['message']} → {i['fix']}")
        print(f"validate: {'OK' if not has_error else 'FAIL'}")
    sys.exit(3 if has_error else 0)


def main(argv=None):
    p = Parser(prog="flowguard_state")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="在 docs/project/ 创建项目级十阶段文档（幂等）")
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("discover", help="只读发现 Git / SDD / 工具状态，不执行初始化")
    sp.set_defaults(fn=cmd_discover)

    sp = sub.add_parser("context", help="治理上下文 bind|show|list|approve|complete")
    sp.add_argument("action", choices=["bind", "show", "list", "approve", "complete"])
    sp.add_argument("--session")
    sp.add_argument("--task-id")
    sp.add_argument("--task-type", choices=context.TASK_TYPES)
    sp.add_argument("--spec-system", choices=context.SPEC_SYSTEMS)
    sp.add_argument("--spec-ref")
    sp.add_argument("--context-id")
    sp.add_argument("--parent-id")
    sp.add_argument("--depends-on", nargs="*", default=[])
    sp.add_argument("--require-evidence", nargs="*", default=[])
    sp.add_argument("--approval")
    sp.add_argument("--actor")
    sp.set_defaults(fn=cmd_context)

    sp = sub.add_parser("evidence", help="证据 record|list（绑定当前代码指纹）")
    sp.add_argument("action", choices=["record", "list"])
    sp.add_argument("--context-id", required=True)
    sp.add_argument("--kind", choices=evidence.KINDS)
    sp.add_argument("--producer")
    sp.add_argument("--result", choices=evidence.RESULTS)
    sp.add_argument("--summary")
    sp.add_argument("--source-ref")
    expiry = sp.add_mutually_exclusive_group()
    expiry.add_argument("--expires-on-change", dest="expires_on_change", action="store_true")
    expiry.add_argument("--no-expire-on-change", dest="expires_on_change", action="store_false")
    sp.set_defaults(fn=cmd_evidence, expires_on_change=None)

    sp = sub.add_parser("governance", help="新治理动作检查（read/spec/test/code/commit/release）")
    sp.add_argument("--session", required=True)
    sp.add_argument("--action", required=True, choices=governance.ACTIONS)
    sp.add_argument("--path")
    sp.set_defaults(fn=cmd_governance)

    sp = sub.add_parser("stage", help="从 docs/ 读取或推进十阶段文档")
    sp.add_argument("action", choices=["status", "advance"])
    sp.add_argument("--task-id", required=True)
    sp.add_argument("--stage", choices=tuple(registry.ARTIFACTS))
    sp.add_argument("--status", choices=stage_docs.VALID_STATUSES)
    sp.add_argument("--approval-ref")
    sp.add_argument("--reason")
    sp.set_defaults(fn=cmd_stage)

    sp = sub.add_parser("validate", help="产物校验（内容/追溯/结论/Tier2 缺失）")
    sp.add_argument("--task-id")
    sp.set_defaults(fn=cmd_validate)

    for name in ("init", "discover", "context", "evidence", "governance", "stage", "validate"):
        sub.choices[name].add_argument("--json", action="store_true")

    args = p.parse_args(argv)
    global _AS_JSON
    _AS_JSON = bool(getattr(args, "json", False))
    try:
        args.fn(args)
    except (state.StateError, context.ContextError, evidence.EvidenceError,
            stage_docs.StageDocError) as e:
        _die(mk_env("ERROR", "state_error", str(e), "检查 docs/ 阶段文档或宿主会话缓存"))


if __name__ == "__main__":
    main()
