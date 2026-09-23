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
    context, detect, discovery, evidence, gate, governance, ids, instructions,
    journal, migration, registry, stage_docs, state, validation,
)
from flowguard_lib.diag import emit as emit_diag, envelope as mk_env  # noqa: E402
from templates import artifacts  # noqa: E402

FEATURE_STAGES = ("requirements", "solution", "testcases", "hld", "lld", "review", "docs")
PROJECT_STAGES = ("architecture", "standards", "release")
OK_STATUSES = ("accepted", "skipped", "overridden")
FEATURE_ARTIFACTS = [aid for aid, a in registry.ARTIFACTS.items() if a["scope"] == "feature"]


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


def _artifact_path(root, rel):
    return root / ".flowguard" / rel


def cmd_init(args):
    root = Path.cwd()
    created = stage_docs.ensure_project(root)
    _out({"initialized": True, "root": str(root), "created": created}, args.json)


def cmd_legacy_init(args):
    root = Path.cwd()
    if not (root / ".flowguard").is_dir():
        _die(mk_env("ERROR", "legacy_state_required",
                    "新项目不创建 .flowguard/；legacy-init 仅用于已有旧项目",
                    "运行 discover/context bind 创建 docs/ 阶段文档；旧项目先运行 migrate --dry-run"))
    project = artifacts.init_project(root)
    journal.append(root, "project", "init", {"modules": list(project["modules"])})
    _out({"initialized": True, "project": project["project"],
          "modules": list(project["modules"]), "stack": project["stack"]}, args.json)


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


def cmd_migrate(args):
    data = migration.apply(Path.cwd()) if args.apply else migration.preview(Path.cwd())
    _out(data, args.json)


def cmd_status(args):
    root = Path.cwd()
    project = state.load_project(root)
    scope = list((project.get("features") or {}).keys())
    if getattr(args, "feature", None):
        if args.feature not in scope:
            _die(mk_env("ERROR", "unknown_feature", f"功能不存在: {args.feature}",
                        "用 /flowguard-feature list 查看功能清单"))
        scope = [args.feature]
    out = {"project": project["project"], "current_feature": project.get("current_feature"),
           "project_stages": {s: project["stages"][s]["status"] for s in PROJECT_STAGES},
           "features": {}}
    for fid in scope:
        try:
            f = state.load_feature(root, fid)
        except state.StateError:
            continue
        req_text = _read(_artifact_path(
            root, f"features/{fid}/" + f["stages"]["requirements"].get("artifact", "artifacts/01-requirements.md")))
        reqs = validation.requirement_ids(req_text)
        tc_text = _read(_artifact_path(
            root, f"features/{fid}/" + f["stages"]["testcases"].get("artifact", "artifacts/04-testcases.md")))
        cov = sum(1 for r in reqs if f"- REQ: {r}" in tc_text)
        out["features"][fid] = {"status": f.get("status"), "modules": f.get("modules"),
                                "stages": {s: f["stages"][s]["status"] for s in FEATURE_STAGES},
                                "req_total": len(reqs), "req_covered": cov}
    _out(out, args.json)


def cmd_feature(args):
    root = Path.cwd()
    project = state.load_project(root)
    if args.action == "new":
        if not ids.is_kebab(args.id):
            _die(mk_env("ERROR", "bad_feature_id", f"功能 id 非法: {args.id}", ids.KEBAB_FIX))
        unknown = [m for m in args.modules if m not in project["modules"]]
        if unknown:
            _die(mk_env("ERROR", "unknown_module", f"模块未注册: {', '.join(unknown)}",
                        "先在 project.json.modules 登记（/flowguard-init 自动探测）"))
        if args.id in (project.get("features") or {}):
            _die(mk_env("ERROR", "feature_exists", f"功能已存在: {args.id}", "换一个 id"))
        fdir = f"features/{args.id}"
        (root / ".flowguard" / fdir / "artifacts").mkdir(parents=True, exist_ok=True)
        stages = {s: {"status": "pending"} for s in FEATURE_STAGES}
        for aid in FEATURE_ARTIFACTS:
            rel = registry.ARTIFACTS[aid]["rel_tpl"].format(feature=args.id)
            stages[registry.ARTIFACTS[aid]["stage"]]["artifact"] = rel.removeprefix(f"{fdir}/")
            p = _artifact_path(root, rel)
            if not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(artifacts.render(aid, {
                    "feature": args.id, "title": args.title or args.id,
                    "modules": ",".join(args.modules),
                    "req_prefix": "<feature-id>/REQ"}), encoding="utf-8")
        feature = {"version": 1, "feature": args.id, "title": args.title or args.id,
                   "modules": args.modules, "status": "active", "stages": stages}
        state.save_feature(root, feature)
        project.setdefault("features", {})[args.id] = {"status": "active", "path": fdir}
        if not project.get("current_feature"):
            project["current_feature"] = args.id
        state.save_project(root, project)
        journal.append(root, f"feature:{args.id}", "feature_new", {"modules": args.modules})
        _out({"feature": args.id, "status": "active", "artifacts": len(FEATURE_ARTIFACTS)}, args.json)
    elif args.action == "list":
        _out(project.get("features") or {}, args.json)
    elif args.action in ("done", "drop"):
        f = state.load_feature(root, args.id)
        if args.action == "drop":
            if not getattr(args, "reason", ""):
                _die(mk_env("ERROR", "reason_required", "drop 必须填写理由", "--reason <理由>"))
            f["status"] = "dropped"
            f["drop_reason"] = args.reason
        else:
            notok = [s for s in FEATURE_STAGES if f["stages"][s]["status"] not in OK_STATUSES]
            if notok:
                _die(mk_env("ERROR", "feature_not_done", f"未验收阶段: {', '.join(notok)}",
                            f"先验收 {notok[0]}（/flowguard-advance --feature {args.id}）"))
            f["status"] = "done"
        state.save_feature(root, f)
        project["features"][args.id]["status"] = f["status"]
        state.save_project(root, project)
        journal.append(root, f"feature:{args.id}", f"feature_{args.action}",
                       {"reason": getattr(args, "reason", "")})
        _out({"feature": args.id, "status": f["status"]}, args.json)


def cmd_next(args):
    root = Path.cwd()
    project = state.load_project(root)
    fid = args.feature or project.get("current_feature")
    if fid and args.stage in (None, *FEATURE_STAGES):
        f = state.load_feature(root, fid)
        if f.get("status") != "active":
            _die(mk_env("ERROR", "feature_inactive", f"功能 {fid} 状态 {f.get('status')}",
                        "选择 active 功能或新建功能"))
        project["current_feature"] = fid
        state.save_project(root, project)
        stage = next((s for s in FEATURE_STAGES if f["stages"][s]["status"] == "pending"), None)
        if stage:
            state.transition_stage(f, stage, "in_progress")
            state.save_feature(root, f)
        aid = next((a for a in FEATURE_ARTIFACTS if registry.ARTIFACTS[a]["stage"] == stage),
                   "01-requirements")
        ins = instructions.build(root, aid, feature=fid)
        journal.append(root, f"feature:{fid}", "next", {"stage": stage})
        _out({"feature": fid, "stage": stage, "instructions": ins}, args.json)
    elif args.stage:
        if args.stage not in PROJECT_STAGES:
            _die(mk_env("ERROR", "bad_stage", f"项目级阶段非法: {args.stage}", f"可选 {PROJECT_STAGES}"))
        if project["stages"][args.stage]["status"] == "pending":
            state.transition_stage(project, args.stage, "in_progress")
        state.save_project(root, project)
        aid = next(a for a, v in registry.ARTIFACTS.items() if v["stage"] == args.stage)
        journal.append(root, "project", "next", {"stage": args.stage})
        _out({"stage": args.stage, "instructions": instructions.build(root, aid)}, args.json)
    else:
        _die(mk_env("ERROR", "usage", "next 需要 --feature 或 --stage", "见 --help"))


def cmd_advance(args):
    """用户验收入口：accepted 的唯一写入点。"""
    root = Path.cwd()
    project = state.load_project(root)
    with state.state_lock(root):
        fid = args.feature or project.get("current_feature")
        use_feature = bool(fid) and args.stage in (None, *FEATURE_STAGES)
        if use_feature:
            f = state.load_feature(root, fid)
            stage = args.stage or next(
                (s for s in FEATURE_STAGES
                 if f["stages"][s]["status"] in ("in_progress", "pending_acceptance")), None)
            if stage is None:
                nxt = next((s for s in FEATURE_STAGES if f["stages"][s]["status"] == "pending"), None)
                _die(mk_env("ERROR", "stage_not_started",
                            f"无可验收阶段（下一阶段 {nxt} 尚未开始）",
                            f"先用 /flowguard-next --feature {fid} 开始"))
            if f["stages"][stage]["status"] == "pending":
                _die(mk_env("ERROR", "stage_not_started", f"阶段 {stage} 尚未开始",
                            "先用 /flowguard-next 开始该阶段"))
            if f["stages"][stage]["status"] == "in_progress":
                state.transition_stage(f, stage, "pending_acceptance")
            state.transition_stage(f, stage, "accepted", reason="用户验收", evidence=args.evidence)
            feature_done = all(f["stages"][s]["status"] in OK_STATUSES for s in FEATURE_STAGES)
            if feature_done:
                f["status"] = "done"
                project["features"][fid]["status"] = "done"
            state.save_feature(root, f)
            state.save_project(root, project)
            journal.append(root, f"feature:{fid}", "accepted_by_user", {"stage": stage})
            _out({"feature": fid, "stage": stage, "status": "accepted",
                  "feature_status": f["status"]}, args.json)
        else:
            stage = args.stage or next(
                (s for s in PROJECT_STAGES
                 if project["stages"][s]["status"] in ("in_progress", "pending_acceptance")), None)
            if stage is None or project["stages"][stage]["status"] == "pending":
                _die(mk_env("ERROR", "stage_not_started", f"项目级阶段 {stage} 尚未开始",
                            "先用 /flowguard-next --stage X 开始"))
            if project["stages"][stage]["status"] == "in_progress":
                state.transition_stage(project, stage, "pending_acceptance")
            state.transition_stage(project, stage, "accepted",
                                   reason="用户验收", evidence=args.evidence)
            state.save_project(root, project)
            journal.append(root, "project", "accepted_by_user", {"stage": stage})
            _out({"stage": stage, "status": "accepted"}, args.json)


def cmd_override(args):
    root = Path.cwd()
    project = state.load_project(root)
    with state.state_lock(root):
        fid = args.feature or project.get("current_feature")
        use_feature = bool(fid) and args.stage in (None, *FEATURE_STAGES)
        if use_feature:
            f = state.load_feature(root, fid)
            stage = args.stage or next(
                (s for s in FEATURE_STAGES if f["stages"][s]["status"] not in OK_STATUSES), None)
            if stage is None:
                _die(mk_env("ERROR", "usage", "功能所有阶段已收敛", "无需 override"))
            state.transition_override(f, stage, reason=args.reason)
            state.save_feature(root, f)
            journal.append(root, f"feature:{fid}", "override",
                           {"stage": stage, "reason": args.reason})
            _out({"feature": fid, "stage": stage, "status": "overridden"}, args.json)
        else:
            stage = args.stage or next(
                (s for s in PROJECT_STAGES if project["stages"][s]["status"] not in OK_STATUSES), None)
            if stage is None:
                _die(mk_env("ERROR", "usage", "项目所有阶段已收敛", "无需 override"))
            state.transition_override(project["stages"], stage, reason=args.reason)
            state.save_project(root, project)
            journal.append(root, "project", "override", {"stage": stage, "reason": args.reason})
            _out({"stage": stage, "status": "overridden"}, args.json)


def cmd_gate(args):
    root = Path.cwd()
    if args.action:
        res = gate.check_action(root, args.action, path=args.path, feature=args.feature)
        if res["allowed"]:
            _out({"allowed": True, "action": args.action}, args.json)
            return
        _die(res["envelope"], code=2, as_json=args.json)
    project = state.load_project(root)
    checks = {}
    for action in ("write_code", "write_review", "write_docs", "build_release"):
        res = gate.check_action(root, action, path=args.path, feature=args.feature)
        checks[action] = res["allowed"]
    _out({"project": project["project"], "current_feature": project.get("current_feature"),
          "actions": checks}, args.json)


def cmd_validate(args):
    root = Path.cwd()
    project = state.load_project(root)
    issues = []
    scope = [args.feature] if args.feature else list((project.get("features") or {}).keys())
    for fid in scope:
        f = state.load_feature(root, fid)
        adir = root / ".flowguard" / "features" / fid / "artifacts"
        req_text = _read(adir / "01-requirements.md")
        reqs = validation.requirement_ids(req_text)
        issues += validation.validate_requirements(req_text, fid)
        issues += validation.validate_testcases(_read(adir / "04-testcases.md"), reqs, root=root)
        issues += validation.validate_review(_read(adir / "08-review.md"))
        stage_now = next((s for s in FEATURE_STAGES if f["stages"][s]["status"] == "in_progress"), None)
        if stage_now:
            issues += validation.missing_tier2(
                [(sk, pkg, registry.install_cmd(sk, pkg))
                 for sk, pkg in registry.TIER2_REFS.get(stage_now, [])], root=root)
    has_error = any(i["level"] == "ERROR" for i in issues)
    if args.json:
        print(json.dumps({"issues": issues, "ok": not has_error}, ensure_ascii=False, indent=2))
    else:
        for i in issues:
            print(f"{i['level']}: [{i['path']}] {i['message']} → {i['fix']}")
        print(f"validate: {'OK' if not has_error else 'FAIL'}")
    sys.exit(3 if has_error else 0)


def cmd_instructions(args):
    try:
        ins = instructions.build(Path.cwd(), args.artifact, feature=args.feature)
    except KeyError:
        _die(mk_env("ERROR", "unknown_artifact", f"未知 artifact: {args.artifact}",
                    "artifact 取值为 01-requirements ~ 10-release"))
    print(json.dumps(ins, ensure_ascii=False, indent=2))


def main(argv=None):
    p = Parser(prog="flowguard_state")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="在 docs/project/ 创建项目级十阶段文档（幂等）")
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("legacy-init", help="仅旧项目兼容：初始化 .flowguard/ 状态")
    sp.set_defaults(fn=cmd_legacy_init)

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

    sp = sub.add_parser("migrate", help="预检或复制旧 .flowguard 产物至 docs/")
    mode = sp.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    sp.set_defaults(fn=cmd_migrate)

    sp = sub.add_parser("status", help="流程看板")
    sp.add_argument("--feature")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("feature", help="功能生命周期 new|list|done|drop")
    sp.add_argument("action", choices=["new", "list", "done", "drop"])
    sp.add_argument("id", nargs="?")
    sp.add_argument("--modules", nargs="+")
    sp.add_argument("--title")
    sp.add_argument("--reason")
    sp.set_defaults(fn=cmd_feature)

    sp = sub.add_parser("next", help="开始阶段（设 current_feature / 项目阶段 in_progress）")
    sp.add_argument("--feature")
    sp.add_argument("--stage")
    sp.set_defaults(fn=cmd_next)

    sp = sub.add_parser("advance", help="用户验收：accepted 唯一写入点")
    sp.add_argument("--feature")
    sp.add_argument("--stage")
    sp.add_argument("--evidence", nargs="*")
    sp.set_defaults(fn=cmd_advance)

    sp = sub.add_parser("override", help="逃生通道（必须 --reason，留痕）")
    sp.add_argument("--feature")
    sp.add_argument("--stage")
    sp.add_argument("--reason", required=True)
    sp.set_defaults(fn=cmd_override)

    sp = sub.add_parser("gate", help="门禁自检")
    sp.add_argument("--feature")
    sp.add_argument("--action", choices=["write_code", "write_review", "write_docs", "build_release"])
    sp.add_argument("--path")
    sp.set_defaults(fn=cmd_gate)

    sp = sub.add_parser("validate", help="产物校验（含追溯/执行证据/Tier2 缺失）")
    sp.add_argument("--feature")
    sp.set_defaults(fn=cmd_validate)

    sp = sub.add_parser("instructions", help="机读指令（context/rules/template/requires/unlocks/tier2）")
    sp.add_argument("artifact")
    sp.add_argument("--feature")
    sp.set_defaults(fn=cmd_instructions)

    for name in ("init", "legacy-init", "discover", "context", "evidence", "governance", "stage", "migrate", "status",
                 "feature", "next", "advance", "override", "gate", "validate", "instructions"):
        sub.choices[name].add_argument("--json", action="store_true")

    args = p.parse_args(argv)
    global _AS_JSON
    _AS_JSON = bool(getattr(args, "json", False))
    try:
        args.fn(args)
    except (state.StateError, context.ContextError, evidence.EvidenceError,
            stage_docs.StageDocError, migration.MigrationError) as e:
        _die(mk_env("ERROR", "state_error", str(e), "检查 docs/ 阶段文档、宿主会话缓存或旧 journal"))


if __name__ == "__main__":
    main()
