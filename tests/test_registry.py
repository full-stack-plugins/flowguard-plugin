import unittest
from scripts.flowguard_lib import registry

def mk_project(std="in_progress", arch="accepted", features=None):
    return {"version": 1, "modules": {"order": {"src_roots": ["server/order"], "stack": "java"},
                                       "web": {"src_roots": ["web/src"], "stack": "vue3"}},
            "stages": {"architecture": {"status": arch}, "standards": {"status": std}, "release": {"status": "pending"}},
            "features": features or {}}

def mk_feature(fid="order-refund", modules=("order",), status="active", stages=None):
    base = {s: {"status": "accepted"} for s in ("requirements", "solution", "testcases", "hld", "lld")}
    base["review"] = {"status": "pending"}
    base["docs"] = {"status": "pending"}
    if stages:
        base.update(stages)
    return {"version": 1, "feature": fid, "modules": list(modules), "status": status, "stages": base}

class StructureTest(unittest.TestCase):
    def test_ten_artifacts(self):
        self.assertEqual(len(registry.ARTIFACTS), 10)
        self.assertEqual(registry.STAGE_ORDER[2], "solution")
        self.assertEqual(registry.STAGE_ORDER[4:6], ("hld", "lld"))

    def test_acyclic_real_registry(self):
        registry.check_acyclic()  # 不抛即通过

    def test_acyclic_detects_cycle(self):
        bad = {"a": {"requires": ("b",)}, "b": {"requires": ("a",)}}
        with self.assertRaises(registry.StateError):
            registry._check_acyclic_graph(bad)

    def test_topo_requirements_before_testcases(self):
        order = registry.topo_order()
        self.assertLess(order.index("01-requirements"), order.index("04-testcases"))
        self.assertLess(order.index("05-hld"), order.index("06-lld"))

class ArtifactStatusTest(unittest.TestCase):
    def test_blocked_and_ready(self):
        proj = mk_project()
        feat = mk_feature(stages={"solution": {"status": "pending"},
                                  "requirements": {"status": "pending"}})
        # 03-solution requires 01-requirements(文件存在) + 02-architecture(项目阶段 accepted)
        status, missing = registry.artifact_status("03-solution", proj, feat)
        self.assertEqual(status, "blocked")
        self.assertIn("01-requirements", missing)
        feat["stages"]["requirements"]["status"] = "accepted"
        (self  # 占位保持可读
        )
        import pathlib, tempfile
        root = pathlib.Path(tempfile.mkdtemp())
        (root / ".flowguard" / "features" / "order-refund" / "artifacts").mkdir(parents=True)
        (root / ".flowguard" / "features" / "order-refund" / "artifacts" / "01-requirements.md").write_text("x")
        status, missing = registry.artifact_status("03-solution", proj, feat, root=root)
        self.assertEqual(status, "ready", missing)

    def test_done_and_skipped(self):
        import pathlib, tempfile
        proj = mk_project()
        feat = mk_feature()
        root = pathlib.Path(tempfile.mkdtemp())
        d = root / ".flowguard" / "features" / "order-refund" / "artifacts"
        d.mkdir(parents=True)
        (d / "01-requirements.md").write_text("x")
        status, _ = registry.artifact_status("01-requirements", proj, feat, root=root)
        self.assertEqual(status, "done")
        feat2 = mk_feature(stages={"hld": {"status": "skipped", "reason": "r"}})
        status, _ = registry.artifact_status("05-hld", proj, feat2, root=root)
        self.assertEqual(status, "skipped")

class UnlockTest(unittest.TestCase):
    def test_write_code_happy(self):
        ok, env = registry.unlock_check("write_code", mk_project(), mk_feature(), path="server/order/A.java")
        self.assertTrue(ok, env)

    def test_write_code_other_path_allowed(self):
        ok, env = registry.unlock_check("write_code", mk_project(), mk_feature(), path="README.md")
        self.assertTrue(ok)
        self.assertIsNone(env)

    def test_write_code_no_feature(self):
        ok, env = registry.unlock_check("write_code", mk_project(), None, path="server/order/A.java")
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_write_code_no_module")

    def test_write_code_module_mismatch(self):
        ok, env = registry.unlock_check("write_code", mk_project(), mk_feature(), path="web/src/App.vue")
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_write_code_feature_mismatch")

    def test_write_code_tdd_gate(self):
        f = mk_feature(stages={"testcases": {"status": "in_progress"}})
        ok, env = registry.unlock_check("write_code", mk_project(), f, path="server/order/A.java")
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_write_code_tdd")

    def test_write_code_needs_standards(self):
        ok, env = registry.unlock_check("write_code", mk_project(std="pending"), mk_feature(), path="server/order/A.java")
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_write_code_no_standards")

    def test_write_review_chain(self):
        f = mk_feature(stages={"lld": {"status": "in_progress"}})
        ok, env = registry.unlock_check("write_review", mk_project(), f)
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_review_needs_testcases")
        ok, env = registry.unlock_check("write_review", mk_project(std="pending"), mk_feature())
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_review_needs_standards")
        ok, _ = registry.unlock_check("write_review", mk_project(arch="accepted", std="accepted"), mk_feature())
        self.assertTrue(ok)

    def test_write_docs_needs_review(self):
        ok, env = registry.unlock_check("write_docs", mk_project(), mk_feature())
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_docs_needs_review")
        f = mk_feature(stages={"review": {"status": "accepted"}})
        ok, _ = registry.unlock_check("write_docs", mk_project(), f)
        self.assertTrue(ok)

    def test_build_release_needs_no_active(self):
        proj = mk_project(std="accepted", features={"order-refund": {"status": "active", "path": "features/order-refund"}})
        ok, env = registry.unlock_check("build_release", proj, None)
        self.assertFalse(ok)
        self.assertEqual(env["code"], "gate_release_active_features")
        proj["features"]["order-refund"]["status"] = "done"
        ok, _ = registry.unlock_check("build_release", proj, None)
        self.assertTrue(ok)

if __name__ == "__main__":
    unittest.main()
