"""错误路径与诊断信封契约：一切 CLI/hook 错误必须走 {severity,code,message,fix}，不裸崩。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
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
        bound = run(self.root, "context", "bind", "--session", "s", "--task-id", "f1",
                    "--task-type", "simple_change", "--spec-system", "none", "--json")
        self.assertEqual(bound.returncode, 0, bound.stderr)

    def _envelope(self, result):
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        env = json.loads(result.stdout)
        self.assertEqual(set(env), {"severity", "code", "message", "fix"})
        self.assertNotIn("Traceback", result.stderr)
        return env

    def test_unknown_task_gets_envelope(self):
        env = self._envelope(run(self.root, "stage", "status", "--task-id", "nope", "--json"))
        self.assertEqual(env["code"], "state_error")

    def test_stage_advance_requires_approval_ref(self):
        env = self._envelope(run(
            self.root, "stage", "advance", "--task-id", "f1",
            "--stage", "01-requirements", "--status", "accepted", "--json"))
        self.assertIn("批准", env["message"])

    def test_evidence_record_unknown_context_gets_envelope(self):
        env = self._envelope(run(
            self.root, "evidence", "record", "--context-id", "missing",
            "--kind", "tests", "--producer", "t", "--result", "pass",
            "--summary", "s", "--source-ref", "r", "--json"))
        self.assertEqual(env["code"], "state_error")

    def test_context_show_unbound_gets_envelope(self):
        env = self._envelope(run(self.root, "context", "show", "--json"))
        self.assertEqual(env["code"], "context_not_bound")

    def test_usage_error_exit3_with_envelope(self):
        r = run(self.root, "bogus-cmd")
        self.assertEqual(r.returncode, 3)
        self.assertIn("ERROR:", r.stderr)  # 人类模式：stderr 两行（Error/Fix 约定）
        self.assertIn("Fix:", r.stderr)
        r2 = run(self.root, "bogus-cmd", "--json")
        self.assertEqual(r2.returncode, 3)
        self.assertEqual(json.loads(r2.stdout)["code"], "usage")
        self.assertNotIn("Traceback", r.stderr + r2.stderr)


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
        state_home = Path(tempfile.mkdtemp())
        old_home = os.environ.get("FLOWGUARD_STATE_HOME")
        os.environ["FLOWGUARD_STATE_HOME"] = str(state_home)
        try:
            sys.path.insert(0, str(REPO / "scripts"))
            from flowguard_lib import runtime
            index = runtime.repository_state_dir(root) / "contexts" / "index.json"
        finally:
            if old_home is None:
                os.environ.pop("FLOWGUARD_STATE_HOME", None)
            else:
                os.environ["FLOWGUARD_STATE_HOME"] = old_home
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("{broken", encoding="utf-8")
        env = dict(os.environ, FLOWGUARD_STATE_HOME=str(state_home))
        for hook in ("flowguard_status_summary.py", "flowguard_prompt_guard.py", "flowguard_stage_summary.py"):
            p = subprocess.run(
                [sys.executable, str(HOOKS / hook)],
                input=json.dumps({"cwd": str(root), "session_id": "s"}),
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(p.returncode, 0, f"{hook}: {p.stderr}")
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
