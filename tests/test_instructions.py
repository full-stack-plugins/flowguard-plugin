import tempfile, unittest
from pathlib import Path
from scripts.flowguard_lib import instructions, yamlmini

CONFIG = """\
schema: flowguard
context: |
  Tech stack: Python + Vue
rules:
  specs:
    - 每条 REQ 必须带验收标准
"""

class InstructionsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / ".flowguard").mkdir()

    def test_injects_config_context_and_rules(self):
        (self.root / ".flowguard" / "config.yaml").write_text(CONFIG, encoding="utf-8")
        ins = instructions.build(self.root, "01-requirements", feature="order-refund")
        self.assertIn("Tech stack: Python + Vue", ins["context"])
        self.assertEqual(ins["rules"]["specs"][0], "每条 REQ 必须带验收标准")
        self.assertEqual(ins["scope"], "feature")
        self.assertEqual(ins["stage"], "requirements")
        self.assertTrue(ins["template"].endswith("01-requirements.md"))
        self.assertTrue(any("feature-design" == t[0] for t in ins["tier2"]))
        for _skill, _pkg, cmd in ins["tier2"]:
            self.assertTrue(cmd.startswith("npx skills add full-stack-skills/"))

    def test_missing_config_gives_empty(self):
        ins = instructions.build(self.root, "02-architecture")
        self.assertEqual(ins["context"], "")
        self.assertEqual(ins["rules"], {})
        self.assertEqual(ins["scope"], "project")
        self.assertEqual(yamlmini.load.__module__, "scripts.flowguard_lib.yamlmini")

if __name__ == "__main__":
    unittest.main()
