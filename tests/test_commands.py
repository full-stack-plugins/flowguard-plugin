import json, pathlib, re, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CMD = ROOT / "commands"
CLI_SRC = (ROOT / "scripts" / "flowgate_state.py").read_text(encoding="utf-8")

EXPECTED = {"flowgate-init", "flowgate-feature", "flowgate-status", "flowgate-next",
            "flowgate-advance", "flowgate-gate", "flowgate-override"}

class CommandsTest(unittest.TestCase):
    def test_all_seven_exist_with_schema(self):
        files = {p.stem for p in CMD.glob("flowgate-*.json")}
        self.assertEqual(files, EXPECTED)
        for p in CMD.glob("flowgate-*.json"):
            d = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(d["name"], p.stem, p)
            self.assertTrue(d.get("description"), p)
            self.assertTrue(d.get("prompt"), p)
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", d["prompt"], p)

    def test_prompt_cli_subcommands_all_exist(self):
        registered = set(re.findall(r'add_parser\("([a-z]+)"', CLI_SRC))
        for p in CMD.glob("flowgate-*.json"):
            prompt = json.loads(p.read_text(encoding="utf-8"))["prompt"]
            for m in re.finditer(r"flowgate_state\.py\"\s+([a-z]+)", prompt):
                self.assertIn(m.group(1), registered, f"{p.stem}: 子命令 {m.group(1)} 未注册")

    def test_advance_requires_user_confirmation(self):
        d = json.loads((CMD / "flowgate-advance.json").read_text(encoding="utf-8"))
        self.assertIn("确认", d["prompt"])
        self.assertIn("不得", d["prompt"])

    def test_override_user_initiated_only(self):
        d = json.loads((CMD / "flowgate-override.json").read_text(encoding="utf-8"))
        self.assertIn("用户", d["prompt"])
        self.assertIn("理由", d["prompt"])

if __name__ == "__main__":
    unittest.main()
