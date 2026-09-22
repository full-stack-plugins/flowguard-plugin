import json, tempfile, unittest
from pathlib import Path
from scripts.flowguard_lib import gate

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

def mk_project(**kw):
    proj = {
        "version": 1,
        "modules": {"order": {"src_roots": ["server/order"], "stack": "java"},
                    "web": {"src_roots": ["web/src"], "stack": "vue3"}},
        "current_feature": "order-refund",
        "stages": {"architecture": {"status": "accepted"},
                   "standards": {"status": kw.get("std", "in_progress")},
                   "release": {"status": "pending"}},
        "features": kw.get("features", {"order-refund": {"status": "active", "path": "features/order-refund"}}),
    }
    return proj

def mk_feature(stages=None):
    base = {s: {"status": "accepted"} for s in ("requirements", "solution", "testcases", "hld", "lld")}
    base["review"] = {"status": "pending"}
    base["docs"] = {"status": "pending"}
    if stages:
        base.update({k: {"status": v} for k, v in stages.items()})
    return {"version": 1, "feature": "order-refund", "modules": ["order"], "status": "active", "stages": base}

class GateTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def _init(self, project=None, feature=None):
        write(self.root / ".flowguard" / "project.json", project or mk_project())
        write(self.root / ".flowguard" / "features" / "order-refund" / "state.json", feature or mk_feature())

    def test_classify_path(self):
        self._init()
        self.assertEqual(gate.classify_path(self.root, ".flowguard/artifacts/01-requirements.md"), "artifact")
        self.assertEqual(gate.classify_path(self.root, "server/order/A.java"), "module:order")
        self.assertEqual(gate.classify_path(self.root, "README.md"), "other")
        self.assertEqual(gate.classify_path(self.root, "web/src/App.vue"), "module:web")

    def test_check_action_matrix(self):
        self._init()
        rows = [
            ("write_code", "server/order/A.java", True, None),
            ("write_code", "web/src/App.vue", False, "gate_write_code_feature_mismatch"),
            ("write_code", "README.md", True, None),
            ("write_code", ".flowguard/artifacts/01-requirements.md", True, None),
        ]
        for action, path, allowed, code in rows:
            res = gate.check_action(self.root, action, path=path)
            self.assertEqual(set(res), {"allowed", "envelope"})
            self.assertEqual(res["allowed"], allowed, f"{action} {path}: {res}")
            got = (res["envelope"] or {}).get("code")
            self.assertEqual(got, code, f"{action} {path}")

    def test_tdd_gate(self):
        self._init(feature=mk_feature({"testcases": "in_progress"}))
        res = gate.check_action(self.root, "write_code", path="server/order/A.java")
        self.assertFalse(res["allowed"])
        self.assertEqual(res["envelope"]["code"], "gate_write_code_tdd")

    def test_no_current_feature(self):
        proj = mk_project()
        proj.pop("current_feature")
        write(self.root / ".flowguard" / "project.json", proj)
        write(self.root / ".flowguard" / "features" / "order-refund" / "state.json", mk_feature())
        res = gate.check_action(self.root, "write_code", path="server/order/A.java")
        self.assertFalse(res["allowed"])
        self.assertEqual(res["envelope"]["code"], "gate_write_code_no_module")

    def test_review_docs_release_chain(self):
        self._init()
        self.assertFalse(gate.check_action(self.root, "write_docs")["allowed"])
        self.assertFalse(gate.check_action(self.root, "build_release")["allowed"])
        f = mk_feature({"review": "accepted", "docs": "accepted"})
        write(self.root / ".flowguard" / "features" / "order-refund" / "state.json", f)
        self.assertTrue(gate.check_action(self.root, "write_docs")["allowed"])
        proj = mk_project(std="accepted",
                          features={"order-refund": {"status": "done", "path": "features/order-refund"}})
        write(self.root / ".flowguard" / "project.json", proj)
        self.assertTrue(gate.check_action(self.root, "build_release")["allowed"])

    def test_uninitialized_flowguard_allows(self):
        res = gate.check_action(self.root, "write_code", path="server/order/A.java")
        self.assertTrue(res["allowed"])
        self.assertIsNone(res["envelope"])

if __name__ == "__main__":
    unittest.main()
