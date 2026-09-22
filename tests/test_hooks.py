import json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"


def run_hook(name, payload):
    p = subprocess.run([sys.executable, str(HOOKS / name)],
                       input=json.dumps(payload, ensure_ascii=False),
                       capture_output=True, text=True)
    return p


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


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

if __name__ == "__main__":
    unittest.main()
