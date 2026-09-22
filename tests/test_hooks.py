import json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"
sys.path.insert(0, str(REPO / "scripts"))

from flowguard_lib import context, evidence  # noqa: E402


def run_hook(name, payload):
    p = subprocess.run([sys.executable, str(HOOKS / name)],
                       input=json.dumps(payload, ensure_ascii=False),
                       capture_output=True, text=True)
    return p


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def mk_git_repo():
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "flowguard@example.test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "FlowGuard Test"], cwd=root, check=True)
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
    return root


def mk_project(current_feature="order-refund", std="pending", features=None):
    return {"version": 1, "project": "demo", "modules": {"app": {"src_roots": ["."], "stack": "java-spring"}},
            "current_feature": current_feature,
            "stages": {"architecture": {"status": "pending"}, "standards": {"status": std},
                       "release": {"status": "pending"}},
            "features": features if features is not None else
                        {"order-refund": {"status": "active", "path": "features/order-refund"}}}


def mk_feature(stages=None):
    base = {s: {"status": "pending"} for s in
            ("requirements", "solution", "testcases", "hld", "lld", "review", "docs")}
    if stages:
        base.update({k: {"status": v} for k, v in stages.items()})
    return {"version": 1, "feature": "order-refund", "modules": ["app"], "status": "active", "stages": base}


class GateHookTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        write(self.root / ".flowguard" / "project.json", mk_project())
        write(self.root / ".flowguard" / "features" / "order-refund" / "state.json", mk_feature())

    def test_block_write_with_envelope(self):
        p = run_hook("flowguard_gate.py", {"tool_name": "Write",
                                          "tool_input": {"file_path": "app/A.java"}, "cwd": str(self.root)})
        self.assertEqual(p.returncode, 2)
        self.assertIn("ERROR:", p.stderr)
        self.assertIn("Fix:", p.stderr)
        self.assertIn("gate_write_code", p.stderr)

    def test_artifact_path_allowed(self):
        p = run_hook("flowguard_gate.py", {"tool_name": "Edit",
                                          "tool_input": {"file_path": ".flowguard/features/order-refund/artifacts/01-requirements.md"},
                                          "cwd": str(self.root)})
        self.assertEqual(p.returncode, 0)

    def test_malformed_stdin_allowed(self):
        p = subprocess.run([sys.executable, str(HOOKS / "flowguard_gate.py")],
                           input="not json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn("WARNING", p.stderr)

    def test_uninitialized_allowed(self):
        empty = Path(tempfile.mkdtemp())
        p = run_hook("flowguard_gate.py", {"tool_name": "Write",
                                          "tool_input": {"file_path": "src/A.java"}, "cwd": str(empty)})
        self.assertEqual(p.returncode, 0)

    def test_bash_release_blocked(self):
        write(self.root / ".flowguard" / "project.json", mk_project(std="accepted"))
        p = run_hook("flowguard_gate.py", {"tool_name": "Bash",
                                          "tool_input": {"command": "mvn deploy -q"}, "cwd": str(self.root)})
        self.assertEqual(p.returncode, 2)
        self.assertIn("gate_release_active_features", p.stderr)

    def test_bash_plain_allowed(self):
        p = run_hook("flowguard_gate.py", {"tool_name": "Bash",
                                          "tool_input": {"command": "ls -la"}, "cwd": str(self.root)})
        self.assertEqual(p.returncode, 0)

    def test_tdd_gate_after_accept(self):
        f = mk_feature({s: "accepted" for s in
                        ("requirements", "solution", "testcases", "hld", "lld")})
        write(self.root / ".flowguard" / "features" / "order-refund" / "state.json", f)
        write(self.root / ".flowguard" / "project.json", mk_project(std="accepted"))
        p = run_hook("flowguard_gate.py", {"tool_name": "Write",
                                          "tool_input": {"file_path": "app/A.java"}, "cwd": str(self.root)})
        self.assertEqual(p.returncode, 0)

class ArtifactCheckHookTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        f = mk_feature({s: "accepted" for s in
                        ("requirements", "solution", "testcases", "hld", "lld", "review", "docs")})
        write(self.root / ".flowguard" / "project.json", mk_project())
        write(self.root / ".flowguard" / "features" / "order-refund" / "state.json", f)
        art = self.root / ".flowguard" / "features" / "order-refund" / "artifacts" / "01-requirements.md"
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text("# 需求", encoding="utf-8")

    def test_rework_degrades_downstream(self):
        p = run_hook("flowguard_artifact_check.py",
                     {"tool_name": "Edit",
                      "tool_input": {"file_path": ".flowguard/features/order-refund/artifacts/01-requirements.md"},
                      "cwd": str(self.root)})
        self.assertEqual(p.returncode, 0)
        f = json.loads((self.root / ".flowguard" / "features" / "order-refund" / "state.json").read_text())
        self.assertEqual(f["stages"]["requirements"]["status"], "in_progress")
        self.assertEqual(f["stages"]["testcases"]["status"], "in_progress")
        self.assertEqual(f["stages"]["docs"]["status"], "in_progress")
        self.assertIn("artifact_rework_degrade",
                      (self.root / ".flowguard" / "journal" / "events.jsonl").read_text())

class SummaryHooksTest(unittest.TestCase):
    def test_status_summary_initialized(self):
        root = Path(tempfile.mkdtemp())
        write(root / ".flowguard" / "project.json", mk_project())
        p = run_hook("flowguard_status_summary.py", {"cwd": str(root)})
        self.assertEqual(p.returncode, 0)
        self.assertIn("[flowguard]", p.stdout)

    def test_status_summary_silent_when_uninitialized(self):
        p = run_hook("flowguard_status_summary.py", {"cwd": str(Path(tempfile.mkdtemp()))})
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")

    def test_stage_summary_next_step(self):
        root = Path(tempfile.mkdtemp())
        write(root / ".flowguard" / "project.json", mk_project())
        write(root / ".flowguard" / "features" / "order-refund" / "state.json", mk_feature())
        p = run_hook("flowguard_stage_summary.py", {"cwd": str(root)})
        self.assertEqual(p.returncode, 0)
        self.assertIn("requirements", p.stdout)


class GovernanceHookTest(unittest.TestCase):
    def test_session_start_discovers_git_project_without_flowguard_init(self):
        root = mk_git_repo()
        p = run_hook("flowguard_status_summary.py", {"cwd": str(root), "session_id": "s"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("SDD 检测", p.stdout)
        self.assertIn("assessment_required", p.stdout)
        self.assertFalse((root / ".flowguard").exists(), "SessionStart 发现必须保持只读")

    def test_user_prompt_submit_reminds_agent_to_reassess_scope(self):
        root = mk_git_repo()
        p = run_hook(
            "flowguard_prompt_guard.py",
            {"cwd": str(root), "session_id": "s", "prompt": "新增退款幂等功能"},
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("重新判断任务", p.stdout)
        self.assertIn("context bind", p.stdout)

    def test_code_write_blocked_but_spec_write_open_before_binding(self):
        root = mk_git_repo()
        blocked = run_hook(
            "flowguard_gate.py",
            {"tool_name": "Write", "tool_input": {"file_path": "src/new.py"},
             "cwd": str(root), "session_id": "s"},
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("governance_context_required", blocked.stderr)

        allowed = run_hook(
            "flowguard_gate.py",
            {"tool_name": "Write",
             "tool_input": {"file_path": "docs/superpowers/specs/change.md"},
             "cwd": str(root), "session_id": "s"},
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_direct_governance_state_tampering_is_blocked(self):
        root = mk_git_repo()
        p = run_hook(
            "flowguard_gate.py",
            {"tool_name": "Edit",
             "tool_input": {"file_path": ".flowguard/contexts/fake.json"},
             "cwd": str(root), "session_id": "s"},
        )
        self.assertEqual(p.returncode, 2)
        self.assertIn("governance_state_protected", p.stderr)

    def test_git_commit_requires_evidence_for_bound_context(self):
        root = mk_git_repo()
        context.bind(
            root, session_id="s", task_id="fix", task_type="simple_change",
            spec_system="none", spec_ref=None,
        )
        p = run_hook(
            "flowguard_gate.py",
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m fix"},
             "cwd": str(root), "session_id": "s"},
        )
        self.assertEqual(p.returncode, 2)
        self.assertIn("tests", p.stderr)
        self.assertIn("semantic_review", p.stderr)

        via_git_c = run_hook(
            "flowguard_gate.py",
            {"tool_name": "Bash", "tool_input": {"command": "git -C . commit -m fix"},
             "cwd": str(root), "session_id": "s"},
        )
        self.assertEqual(via_git_c.returncode, 2)
        self.assertIn("governance_evidence_required", via_git_c.stderr)

    def test_post_write_marks_old_evidence_stale(self):
        root = mk_git_repo()
        ctx = context.bind(
            root, session_id="s", task_id="fix", task_type="simple_change",
            spec_system="none", spec_ref=None,
        )
        rec = evidence.record(
            root, ctx["context_id"], kind="tests", producer="unittest", result="pass",
            summary="passed", source_ref="python3 -m unittest",
        )
        (root / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
        p = run_hook(
            "flowguard_artifact_check.py",
            {"tool_name": "Edit", "tool_input": {"file_path": "src/app.py"},
             "cwd": str(root), "session_id": "s"},
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("证据已过期", p.stderr)
        self.assertEqual(evidence.load(root, ctx["context_id"], rec["evidence_id"])["status"], "stale")

    def test_post_bash_records_only_explicit_test_result_as_evidence(self):
        root = mk_git_repo()
        ctx = context.bind(
            root, session_id="s", task_id="fix", task_type="simple_change",
            spec_system="none", spec_ref=None,
        )
        p = run_hook(
            "flowguard_artifact_check.py",
            {"tool_name": "Bash", "tool_input": {"command": "python3 -m unittest"},
             "tool_response": {"exit_code": 0, "output": "10 tests OK"},
             "cwd": str(root), "session_id": "s"},
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("已记录证据", p.stderr)
        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

    def test_stop_reports_missing_commit_evidence_not_legacy_stage(self):
        root = mk_git_repo()
        context.bind(
            root, session_id="s", task_id="fix", task_type="simple_change",
            spec_system="none", spec_ref=None,
        )
        p = run_hook("flowguard_stage_summary.py", {"cwd": str(root), "session_id": "s"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("缺失提交证据", p.stdout)
        self.assertIn("semantic_review", p.stdout)

if __name__ == "__main__":
    unittest.main()
