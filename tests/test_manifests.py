import json, pathlib, re, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ManifestContractTest(unittest.TestCase):
    def _load(self, rel):
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_zcode_manifest_core_fields(self):
        m = self._load(".zcode-plugin/plugin.json")
        self.assertEqual(m["name"], "flowguard")
        self.assertEqual(m["displayName"], "研发流程门禁")
        # sync-plugin-configs 以 catalog 为单源规范 i18n（en 与 displayName 同值）
        self.assertEqual(m["displayName_i18n"]["en"], "研发流程门禁")
        # 版本不断言字面量（发版脚本每次 bump）；与 catalog 的同步由市场仓 sync-plugin-configs 在发布时强制
        self.assertRegex(m["version"], r"^\d+\.\d+\.\d+$")
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
        self.assertEqual(events, {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"})

    def test_claude_hooks_cover_agent_governance_loop(self):
        hooks = self._load("hooks/hooks.json")["hooks"]
        self.assertEqual(
            set(hooks),
            {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"},
        )

    def test_agents_marketplace_source(self):
        p = self._load(".agents/plugins/marketplace.json")["plugins"][0]
        self.assertEqual(p["name"], "flowguard")
        self.assertRegex(p["source"]["ref"], r"^v\d+\.\d+\.\d+$")

if __name__ == "__main__":
    unittest.main()
