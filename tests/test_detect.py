import json, tempfile, unittest
from pathlib import Path
from scripts.flowguard_lib import detect
from scripts.templates import artifacts

def touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")

class DetectTest(unittest.TestCase):
    def test_java_single_module(self):
        root = Path(tempfile.mkdtemp())
        touch(root / "pom.xml")
        out = detect.detect(root)
        self.assertEqual(list(out["modules"]), ["app"])
        self.assertEqual(out["modules"]["app"]["stack"], "java-spring")
        self.assertEqual(out["stack"]["backend"], "java-spring")

    def test_monorepo_java_plus_vue(self):
        root = Path(tempfile.mkdtemp())
        touch(root / "server" / "order" / "pom.xml")
        pkg = {"dependencies": {"vue": "^3.4.0"}}
        touch(root / "web" / "package.json")
        (root / "web" / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        out = detect.detect(root)
        self.assertEqual(out["modules"]["order"]["stack"], "java-spring")
        self.assertEqual(out["modules"]["web"]["stack"], "vue3")
        self.assertEqual(out["stack"]["backend"], "java-spring")
        self.assertEqual(out["stack"]["frontend"], "vue3")

    def test_unrecognized_falls_back_to_app(self):
        root = Path(tempfile.mkdtemp())
        out = detect.detect(root)
        self.assertEqual(out["modules"], {"app": {"src_roots": ["."], "stack": None}})

    def test_prunes_vendor_dirs(self):
        root = Path(tempfile.mkdtemp())
        touch(root / "node_modules" / "left-pad" / "package.json")
        out = detect.detect(root)
        self.assertEqual(list(out["modules"]), ["app"])

class TemplatesTest(unittest.TestCase):
    def test_all_ten_render(self):
        ctx = {"feature": "order-refund", "title": "订单退款", "modules": "order,payment",
               "req_prefix": "order-refund/REQ"}
        for aid in [f"{i:02d}-{n}" for i, n in enumerate(
                ["requirements", "architecture", "solution", "testcases", "hld", "lld",
                 "standards", "review", "docs", "release"], 1)]:
            text = artifacts.render(aid, ctx)
            self.assertIn("元信息", text, aid)
            self.assertIn("订单退款", text, aid)

    def test_requirements_template_has_format_example(self):
        text = artifacts.render("01-requirements", {"feature": "f", "title": "t",
                                                    "modules": "m", "req_prefix": "f/REQ"})
        self.assertIn("### Requirement:", text)
        self.assertIn("#### Scenario:", text)
        self.assertIn("f/REQ-1", text)

    def test_testcases_template_has_traceability_fields(self):
        text = artifacts.render("04-testcases", {"feature": "f", "title": "t",
                                                 "modules": "m", "req_prefix": "f/REQ"})
        self.assertIn("- REQ:", text)
        self.assertIn("- 测试文件:", text)

class InitProjectTest(unittest.TestCase):
    def test_init_creates_skeleton(self):
        root = Path(tempfile.mkdtemp())
        touch(root / "pom.xml")
        proj = detect.init_project(root)
        self.assertTrue((root / ".flowguard" / "project.json").exists())
        self.assertTrue((root / ".flowguard" / "config.yaml").exists())
        self.assertTrue((root / ".flowguard" / "project" / "02-architecture.md").exists())
        self.assertTrue((root / ".flowguard" / "project" / "07-standards.md").exists())
        self.assertTrue((root / ".flowguard" / "project" / "10-release.md").exists())
        self.assertEqual(proj["modules"]["app"]["stack"], "java-spring")
        self.assertIsNone(proj["current_feature"])
        # 幂等
        proj2 = detect.init_project(root)
        self.assertEqual(proj2, proj)

if __name__ == "__main__":
    unittest.main()
