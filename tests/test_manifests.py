import json, pathlib, re, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ManifestContractTest(unittest.TestCase):
    def _load(self, rel):
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_zcode_manifest_core_fields(self):
        m = self._load(".zcode-plugin/plugin.json")
        self.assertEqual(m["name"], "flowgate")
        self.assertEqual(m["displayName"], "研发流程门禁")
        self.assertEqual(m["displayName_i18n"]["en"], "FlowGate: R&D Process Gate")
        self.assertEqual(m["version"], "0.1.0")
        self.assertEqual(m["license"], "Apache-2.0")
        self.assertNotIn("hooks", m, "ZCode manifest 不得写 hooks 键（约定发现）")
        self.assertNotIn("mcpServers", m)
        self.assertEqual(m["skills"], "skills")
        self.assertEqual(m["commands"], "commands")

    def test_versions_consistent(self):
        z = self._load(".zcode-plugin/plugin.json")["version"]
        k = self._load("kimi.plugin.json")["version"]
        a = self._load(".agents/plugins/marketplace.json")["plugins"][0]["version"]
        c = self._load(".codex-plugin/plugin.json")["version"]
        self.assertEqual(z, k)
        self.assertEqual(z, a)
        self.assertTrue(c.startswith(z + "+codex."),
                        f"codex version {c} 须为 {z}+codex.<YYYYMMDD>")

    def test_kimi_inlines_hooks(self):
        m = self._load("kimi.plugin.json")
        events = {h["event"] for h in m["hooks"]}
        self.assertEqual(events, {"SessionStart", "PreToolUse", "PostToolUse", "Stop"})

    def test_agents_marketplace_source(self):
        p = self._load(".agents/plugins/marketplace.json")["plugins"][0]
        self.assertEqual(p["name"], "flowgate")
        self.assertRegex(p["source"]["ref"], r"^v\d+\.\d+\.\d+$")

if __name__ == "__main__":
    unittest.main()
