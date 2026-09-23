import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from flowguard_lib import stage_docs  # noqa: E402


def run(root, *args):
    return subprocess.run([sys.executable, str(REPO / "scripts/flowguard_state.py"), *args],
                          cwd=root, capture_output=True, text=True)


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        source = self.root / ".flowguard/features/refund/artifacts/01-requirements.md"
        source.parent.mkdir(parents=True)
        source.write_text(
            "# 退款需求\n\n## 1. 文档信息\n\n## 2. 需求\n\n"
            "### Requirement: 幂等退款\n`refund/REQ-1` 系统 SHALL 拒绝重复退款。\n\n"
            "#### Scenario: 重复通知\n- WHEN 收到重复通知\n- THEN 不重复退款\n",
            encoding="utf-8",
        )
        state = self.root / ".flowguard/features/refund/state.json"
        state.write_text(json.dumps({
            "feature": "refund", "stages": {"requirements": {"status": "accepted"}},
        }), encoding="utf-8")

    def test_preview_is_read_only_and_apply_preserves_legacy_content_without_trusting_old_acceptance(self):
        result = run(self.root, "migrate", "--dry-run", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["conflicts"], [])
        self.assertEqual(len(plan["entries"]), 1)
        self.assertFalse((self.root / "docs").exists())

        applied_result = run(self.root, "migrate", "--apply", "--json")
        self.assertEqual(applied_result.returncode, 0, applied_result.stderr)
        applied = json.loads(applied_result.stdout)
        self.assertEqual(len(applied["created"]), 1)
        migrated = self.root / "docs/features/refund/01-requirements.md"
        self.assertIn("拒绝重复退款", migrated.read_text(encoding="utf-8"))
        self.assertEqual(stage_docs.read(self.root, "refund", "01-requirements")["status"], "pending_acceptance")
        self.assertTrue((self.root / ".flowguard/features/refund/artifacts/01-requirements.md").is_file())

    def test_destination_conflict_stops_all_writes(self):
        destination = self.root / "docs/features/refund/01-requirements.md"
        destination.parent.mkdir(parents=True)
        destination.write_text("# user content\n", encoding="utf-8")

        result = run(self.root, "migrate", "--apply", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("冲突", result.stdout + result.stderr)
        self.assertEqual(destination.read_text(encoding="utf-8"), "# user content\n")

    def test_failed_atomic_creation_leaves_legacy_and_destination_intact(self):
        destination = self.root / "docs/features/refund/01-requirements.md"
        source = self.root / ".flowguard/features/refund/artifacts/01-requirements.md"
        before = source.read_bytes()
        from flowguard_lib import migration

        with mock.patch("os.link", side_effect=OSError("link failed")):
            with self.assertRaises(migration.MigrationError):
                migration.apply(self.root)
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse(destination.exists())
        self.assertEqual(list(destination.parent.glob(".flowguard-*")), [])

    def test_migration_cannot_write_while_stage_state_lock_is_held(self):
        from flowguard_lib import state
        destination = self.root / "docs/features/refund/01-requirements.md"
        with state.state_lock(self.root):
            result = run(self.root, "migrate", "--apply", "--json")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(destination.exists())

    def test_failed_later_migration_does_not_delete_externally_changed_document(self):
        from flowguard_lib import migration, state
        second = self.root / ".flowguard/project/02-architecture.md"
        second.parent.mkdir(parents=True)
        second.write_text("# 旧架构\n", encoding="utf-8")
        first_target = self.root / "docs/features/refund/01-requirements.md"
        second_target = self.root / "docs/project/02-architecture.md"
        original_create = state.atomic_create_text
        calls = 0

        def create_then_external_edit(path, content, *, mode=None):
            nonlocal calls
            calls += 1
            if calls == 2:
                first_target.write_text("# 用户并发修改\n", encoding="utf-8")
                raise OSError("second creation failed")
            return original_create(path, content, mode=mode)

        with mock.patch.object(state, "atomic_create_text", side_effect=create_then_external_edit):
            with self.assertRaises(migration.MigrationError) as failure:
                migration.apply(self.root)
        self.assertIn("docs/features/refund/01-requirements.md", str(failure.exception))
        self.assertTrue(first_target.exists(), "迁移回滚删除了用户刚修改的文档")
        self.assertEqual(first_target.read_text(encoding="utf-8"), "# 用户并发修改\n")
        self.assertFalse(second_target.exists())


if __name__ == "__main__":
    unittest.main()
