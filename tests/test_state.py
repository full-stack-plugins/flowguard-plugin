import tempfile, unittest
from pathlib import Path
from scripts.flowgate_lib import state

STATUSES = state.STAGE_STATUSES
LEGAL = {
    ("pending", "in_progress"),
    ("in_progress", "pending_acceptance"),
    ("pending_acceptance", "accepted"),
    ("pending_acceptance", "skipped"),
    ("pending_acceptance", "in_progress"),
    ("accepted", "in_progress"),
    ("skipped", "in_progress"),
    ("overridden", "in_progress"),
}

class TransitionMatrixTest(unittest.TestCase):
    def test_full_6x6_matrix(self):
        for frm in STATUSES:
            for to in STATUSES:
                owner = {"stages": {"s": {"status": frm}}}
                should = (frm, to) in LEGAL
                if should:
                    state.transition_stage(owner, "s", to, reason="r")
                    self.assertEqual(owner["stages"]["s"]["status"], to)
                else:
                    with self.assertRaises(state.StateError, msg=f"{frm}->{to} 应非法"):
                        state.transition_stage(owner, "s", to, reason="r")

    def test_reason_required_for_optout(self):
        owner = {"stages": {"s": {"status": "pending_acceptance"}}}
        for to in ("skipped", "overridden"):
            with self.assertRaises(state.StateError):
                state.transition_stage(owner, "s", to, reason="")

    def test_accepted_writes_accepted_at_and_evidence(self):
        owner = {"stages": {"s": {"status": "pending_acceptance"}}}
        state.transition_stage(owner, "s", "accepted", evidence=["证据1"])
        self.assertIn("accepted_at", owner["stages"]["s"])
        self.assertEqual(owner["stages"]["s"]["evidence"], ["证据1"])

class DegradeTest(unittest.TestCase):
    def test_cascade_full(self):
        owner = {"stages": {s: {"status": "accepted"} for s in
                 ("requirements", "testcases", "review", "docs")}}
        down = state.degrade_from(owner, "requirements")
        self.assertEqual(sorted(down), ["docs", "requirements", "review", "testcases"])
        for s in down:
            self.assertEqual(owner["stages"][s]["status"], "in_progress")

    def test_degrade_only_accepted_or_pending(self):
        owner = {"stages": {"requirements": {"status": "accepted"},
                            "testcases": {"status": "in_progress"},
                            "review": {"status": "pending"},
                            "docs": {"status": "pending_acceptance"}}}
        down = state.degrade_from(owner, "requirements")
        self.assertEqual(sorted(down), ["docs", "requirements"])

class LockAndIOTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_lock_mutex(self):
        with state.state_lock(self.root):
            with self.assertRaises(state.StateError):
                with state.state_lock(self.root):
                    pass

    def test_project_roundtrip(self):
        with self.assertRaises(state.StateError):
            state.load_project(self.root)  # 未初始化
        data = {"version": 1, "project": "demo", "stages": {}}
        state.save_project(self.root, data)
        self.assertEqual(state.load_project(self.root), data)

    def test_feature_roundtrip(self):
        with self.assertRaises(state.StateError):
            state.load_feature(self.root, "nope")
        data = {"version": 1, "feature": "f1", "status": "active", "stages": {}}
        state.save_feature(self.root, data)
        self.assertEqual(state.load_feature(self.root, "f1"), data)

if __name__ == "__main__":
    unittest.main()
