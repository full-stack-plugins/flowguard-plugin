"""阶段状态迁移全矩阵：满足态互跳/重复写必须被拒，回改走 in_progress。"""
import re
import tempfile
import unittest
from pathlib import Path

from flowguard_lib import context, stage_docs


class TransitionMatrixTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        context.bind(self.root, session_id="s", task_id="f1", task_type="simple_change",
                     spec_system="none", spec_ref=None)

    def fill(self, stage="01-requirements"):
        path = stage_docs.path_for(self.root, "f1", stage)
        path.write_text(re.sub(r"\{\{[^}\n]+\}\}", "已确认", path.read_text(encoding="utf-8")),
                        encoding="utf-8")

    def advance(self, target, stage="01-requirements", **kw):
        return stage_docs.advance(self.root, "f1", stage, target, **kw)

    def test_legal_table_covers_all_statuses(self):
        self.assertEqual(set(stage_docs.LEGAL), set(stage_docs.VALID_STATUSES))

    def test_pending_to_accepted_is_legal(self):
        self.fill()
        self.assertEqual(self.advance("accepted", approval_ref="user:1")["status"], "accepted")

    def test_accepted_cannot_be_rewritten_without_content_change(self):
        self.fill()
        self.advance("accepted", approval_ref="user:1")
        with self.assertRaisesRegex(stage_docs.StageDocError, "非法状态迁移 accepted → accepted"):
            self.advance("accepted", approval_ref="user:2")

    def test_satisfied_states_cannot_flip_sideways(self):
        self.fill()
        self.advance("accepted", approval_ref="user:1")
        for target in ("skipped", "inherited"):
            with self.subTest(target=target):
                with self.assertRaisesRegex(stage_docs.StageDocError, "非法状态迁移"):
                    self.advance(target, approval_ref="user:x", reason="r")
        self.advance("in_progress")
        self.advance("skipped", approval_ref="user:skip", reason="范围不适用")
        for target in ("accepted", "inherited", "skipped"):
            with self.subTest(target=target):
                with self.assertRaisesRegex(stage_docs.StageDocError, "非法状态迁移"):
                    self.advance(target, approval_ref="user:x", reason="r")

    def test_rework_must_go_through_in_progress(self):
        self.fill()
        self.advance("accepted", approval_ref="user:1")
        self.assertEqual(self.advance("in_progress")["status"], "in_progress")
        self.assertEqual(self.advance("accepted", approval_ref="user:2")["status"], "accepted")

    def test_invalidated_allows_direct_reaccept(self):
        self.fill()
        self.advance("accepted", approval_ref="user:1")
        path = stage_docs.path_for(self.root, "f1", "01-requirements")
        path.write_text(path.read_text(encoding="utf-8") + "\n新增业务条件。\n", encoding="utf-8")
        self.assertEqual(stage_docs.read(self.root, "f1", "01-requirements")["status"], "invalidated")
        self.assertEqual(self.advance("accepted", approval_ref="user:recheck")["status"], "accepted")

    def test_pending_and_invalidated_are_not_writable_targets(self):
        self.fill()
        self.advance("in_progress")
        for target in ("pending", "invalidated"):
            with self.subTest(target=target):
                with self.assertRaises(stage_docs.StageDocError):
                    self.advance(target)

    def test_pending_acceptance_round_trip(self):
        self.fill()
        self.advance("in_progress")
        self.assertEqual(self.advance("pending_acceptance")["status"], "pending_acceptance")
        self.assertEqual(self.advance("accepted", approval_ref="user:1")["status"], "accepted")


if __name__ == "__main__":
    unittest.main()
