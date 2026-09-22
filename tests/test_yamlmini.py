import unittest
from scripts.flowguard_lib import yamlmini

SAMPLE = """\
schema: flowguard
context: |
  Tech stack: Python
  Team: 3 people
rules:
  specs:
    - 每条 REQ 必须带验收标准
    - 中文书写
tasks:
  - 可勾选
"""

class YamlMiniTest(unittest.TestCase):
    def test_load_sample(self):
        data = yamlmini.load(SAMPLE)
        self.assertEqual(data["schema"], "flowguard")
        self.assertIn("Tech stack: Python", data["context"])
        self.assertIn("Team: 3 people", data["context"])
        self.assertEqual(data["rules"]["specs"][0], "每条 REQ 必须带验收标准")
        self.assertEqual(data["tasks"], ["可勾选"])

    def test_roundtrip(self):
        data = yamlmini.load(SAMPLE)
        self.assertEqual(yamlmini.load(yamlmini.dump(data)), data)

    def test_rejects_unknown_shape(self):
        with self.assertRaises(ValueError):
            yamlmini.load("a:\n  b:\n    c:\n      d: too-deep\n")

    def test_rejects_scalar_list_confusion(self):
        with self.assertRaises(ValueError):
            yamlmini.load("a: 1\n  - item\n")

if __name__ == "__main__":
    unittest.main()
