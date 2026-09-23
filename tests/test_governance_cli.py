import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "scripts" / "flowguard_state.py"


def run(root, *argv):
    return subprocess.run(
        [sys.executable, str(CLI), *argv], cwd=root, capture_output=True, text=True,
    )


class GovernanceCliTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "flowguard@example.test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "FlowGuard Test"], cwd=self.root, check=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.root, check=True)

    def test_discover_bind_approve_and_governance_check(self):
        spec = self.root / "openspec" / "changes" / "refund"
        spec.mkdir(parents=True)
        result = run(self.root, "discover", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["sdd"]["selected_system"], "openspec")

        result = run(
            self.root, "context", "bind", "--session", "s", "--task-id", "refund",
            "--task-type", "important_change", "--spec-system", "openspec",
            "--spec-ref", "openspec/changes/refund", "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        context_id = json.loads(result.stdout)["context_id"]

        denied = run(self.root, "governance", "--session", "s", "--action", "code_write", "--json")
        self.assertEqual(denied.returncode, 2)
        self.assertEqual(json.loads(denied.stdout)["code"], "governance_approval_required")

        approved = run(
            self.root, "context", "approve", "--context-id", context_id,
            "--approval", "scope_approved", "--actor", "user", "--json",
        )
        self.assertEqual(approved.returncode, 0, approved.stderr)
        allowed = run(self.root, "governance", "--session", "s", "--action", "code_write", "--json")
        self.assertEqual(allowed.returncode, 2)
        self.assertEqual(json.loads(allowed.stdout)["code"], "governance_stage_required")

    def test_evidence_record_and_list(self):
        bound = run(
            self.root, "context", "bind", "--session", "s", "--task-id", "fix",
            "--task-type", "simple_change", "--spec-system", "none", "--json",
        )
        context_id = json.loads(bound.stdout)["context_id"]
        recorded = run(
            self.root, "evidence", "record", "--context-id", context_id,
            "--kind", "tests", "--producer", "unittest", "--result", "pass",
            "--summary", "9 passed", "--source-ref", "python3 -m unittest", "--json",
        )
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        listed = run(
            self.root, "evidence", "list", "--context-id", context_id, "--json",
        )
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout)["valid_kinds"], ["tests"])

    def test_stage_command_reads_and_advances_docs_without_private_directory(self):
        bound = run(
            self.root, "context", "bind", "--session", "s", "--task-id", "fix",
            "--task-type", "simple_change", "--spec-system", "none", "--json",
        )
        self.assertEqual(bound.returncode, 0, bound.stderr)
        status = run(self.root, "stage", "status", "--task-id", "fix", "--json")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(len(json.loads(status.stdout)["stages"]), 10)
        started = run(
            self.root, "stage", "advance", "--task-id", "fix",
            "--stage", "01-requirements", "--status", "in_progress", "--json",
        )
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(json.loads(started.stdout)["status"], "in_progress")
        self.assertFalse((self.root / ".flowguard").exists())

    def test_legacy_init_cannot_create_private_directory_in_new_project(self):
        result = run(self.root, "legacy-init", "--json")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["code"], "legacy_state_required")
        self.assertFalse((self.root / ".flowguard").exists())

    def test_init_creates_only_project_stage_documents(self):
        result = run(self.root, "init", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "docs/project/02-architecture.md").is_file())
        self.assertTrue((self.root / "docs/project/07-standards.md").is_file())
        self.assertTrue((self.root / "docs/project/10-release.md").is_file())
        self.assertFalse((self.root / ".flowguard").exists())


if __name__ == "__main__":
    unittest.main()
