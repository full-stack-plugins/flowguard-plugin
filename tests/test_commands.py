import json, pathlib, re, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CMD = ROOT / "commands"
CLI_SRC = (ROOT / "scripts" / "flowguard_state.py").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))

from generate_kimi_commands import render_command  # noqa: E402

EXPECTED = {
    "flowguard-discover", "flowguard-context", "flowguard-evidence", "flowguard-governance",
    "flowguard-init", "flowguard-stage",
}

class CommandsTest(unittest.TestCase):
    def test_kimi_markdown_commands_mirror_json_source(self):
        manifest = json.loads((ROOT / "kimi.plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["commands"], "./kimi-commands/")
        files = {p.stem for p in (ROOT / "kimi-commands").glob("*.md")}
        self.assertEqual(files, EXPECTED)
        for source in CMD.glob("flowguard-*.json"):
            data = json.loads(source.read_text(encoding="utf-8"))
            rendered = (ROOT / "kimi-commands" / (source.stem + ".md")).read_text(encoding="utf-8")
            self.assertEqual(rendered, render_command(data), source.name)
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", rendered)
            self.assertIn("${KIMI_PLUGIN_ROOT}", rendered)

    def test_all_commands_exist_with_schema(self):
        files = {p.stem for p in CMD.glob("flowguard-*.json")}
        self.assertEqual(files, EXPECTED)
        for p in CMD.glob("flowguard-*.json"):
            d = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(d["name"], p.stem, p)
            self.assertTrue(d.get("description"), p)
            self.assertTrue(d.get("prompt"), p)
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", d["prompt"], p)

    def test_prompt_cli_subcommands_all_exist(self):
        registered = set(re.findall(r'add_parser\("([a-z]+)"', CLI_SRC))
        for p in CMD.glob("flowguard-*.json"):
            prompt = json.loads(p.read_text(encoding="utf-8"))["prompt"]
            for m in re.finditer(r"flowguard_state\.py\"\s+([a-z]+)", prompt):
                self.assertIn(m.group(1), registered, f"{p.stem}: 子命令 {m.group(1)} 未注册")


if __name__ == "__main__":
    unittest.main()
