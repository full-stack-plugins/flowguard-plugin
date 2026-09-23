"""错误路径与诊断信封契约：一切 CLI/hook 错误必须走 {severity,code,message,fix}，不裸崩。"""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "scripts" / "flowguard_state.py"
HOOKS = REPO / "hooks"


def run(root, *argv):
    return subprocess.run([sys.executable, str(CLI), *argv], cwd=root,
                          capture_output=True, text=True)


class ErrorPathTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "pom.xml").write_text("<project/>", encoding="utf-8")
        (self.root / ".flowguard").mkdir()  # 显式旧项目夹具
        self.assertEqual(run(self.root, "legacy-init", "--json").returncode, 0)
        self.assertEqual(run(self.root, "feature", "new", "f1", "--modules", "app", "--json").returncode, 0)

    def test_unknown_artifact_gets_envelope(self):
        r = run(self.root, "instructions", "99-bogus", "--json")
        self.assertEqual(r.returncode, 3)
        env = json.loads(r.stdout)
        self.assertEqual(env["code"], "unknown_artifact")
        self.assertEqual(set(env), {"severity", "code", "message", "fix"})
        self.assertNotIn("Traceback", r.stderr)

    def test_status_unknown_feature_gets_envelope(self):
        r = run(self.root, "status", "--feature", "nope", "--json")
        self.assertEqual(r.returncode, 3)
        env = json.loads(r.stdout)
        self.assertEqual(env["code"], "unknown_feature")

    def test_status_feature_filters(self):
        r = run(self.root, "status", "--feature", "f1", "--json")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(list(json.loads(r.stdout)["features"]), ["f1"])

    def test_usage_error_exit3_with_envelope(self):
        r = run(self.root, "bogus-cmd")
        self.assertEqual(r.returncode, 3)
        self.assertIn("ERROR:", r.stderr)  # 人类模式：stderr 两行（Error/Fix 约定）
        self.assertIn("Fix:", r.stderr)
        r2 = run(self.root, "bogus-cmd", "--json")
        self.assertEqual(r2.returncode, 3)
        self.assertEqual(json.loads(r2.stdout)["code"], "usage")
        self.assertNotIn("Traceback", r.stderr + r2.stderr)

    def test_drop_without_reason(self):
        r = run(self.root, "feature", "drop", "f1", "--json")
        self.assertEqual(r.returncode, 3)
        env = json.loads(r.stdout)
        self.assertIn("reason", env["code"].lower() + env["message"].lower())


class HookErrorPathTest(unittest.TestCase):
    def test_gate_half_valid_write_json_is_denied_inside_git_repo(self):
        p = subprocess.run([sys.executable, str(HOOKS / "flowguard_gate.py")],
                           input=json.dumps({"tool_name": "Write"}),  # 缺 tool_input/cwd
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("governance_context_required", p.stderr)
        self.assertNotIn("Traceback", p.stderr)

    def test_artifact_check_bad_json_allows(self):
        p = subprocess.run([sys.executable, str(HOOKS / "flowguard_artifact_check.py")],
                           input="{not json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)

    def test_summary_bad_cwd_silent(self):
        p = subprocess.run([sys.executable, str(HOOKS / "flowguard_status_summary.py")],
                           input=json.dumps({"cwd": "/nonexistent/x"}), capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)

    def test_governance_summary_hooks_fail_open_on_corrupt_context_index(self):
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        index = root / ".flowguard" / "contexts" / "index.json"
        index.parent.mkdir(parents=True)
        index.write_text("{broken", encoding="utf-8")
        for hook in ("flowguard_status_summary.py", "flowguard_prompt_guard.py", "flowguard_stage_summary.py"):
            p = subprocess.run(
                [sys.executable, str(HOOKS / hook)],
                input=json.dumps({"cwd": str(root), "session_id": "s"}),
                capture_output=True, text=True,
            )
            self.assertEqual(p.returncode, 0, f"{hook}: {p.stderr}")
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
