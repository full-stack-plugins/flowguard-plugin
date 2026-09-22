import json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "generate_skills.py"
sys.path.insert(0, str(REPO))

from scripts.generate_skills import generate  # noqa: E402

class ParityTest(unittest.TestCase):
    def test_generated_skills_match_committed(self):
        generated_root = Path(tempfile.mkdtemp())
        generate(generated_root)
        actual = {
            path.relative_to(REPO / "skills"): path.read_text(encoding="utf-8")
            for path in (REPO / "skills").rglob("*") if path.is_file()
        }
        expected = {
            path.relative_to(generated_root / "skills"): path.read_text(encoding="utf-8")
            for path in (generated_root / "skills").rglob("*") if path.is_file()
        }
        self.assertEqual(set(actual), set(expected), "skills/ 文件清单与模板生成结果不一致")
        for path, text in expected.items():
            self.assertEqual(actual[path], text, f"skills/{path} 与模板生成结果不一致")

class SkillFormatTest(unittest.TestCase):
    def test_all_skills_valid(self):
        for d in sorted((REPO / "skills").iterdir()):
            if not d.is_dir():
                continue
            md = d / "SKILL.md"
            self.assertTrue(md.exists(), d)
            text = md.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            self.assertIsNotNone(m, d)
            fm = m.group(1)
            name = re.search(r"^name: (\S+)$", fm, re.M).group(1)
            self.assertEqual(name, d.name, "name 必须与目录同名")
            self.assertIn("license: Apache-2.0", fm)
            desc = re.search(r"^description: (.+)$", fm, re.M).group(1)
            self.assertLessEqual(len(desc), 1024)
            self.assertLessEqual(len(text.splitlines()), 500, d)
            self.assertNotRegex(text, r"\]\(\.\./", "禁止跨技能相对路径")

    def test_artifact_templates_present(self):
        count = 0
        for d in (REPO / "skills").iterdir():
            t = d / "references" / "templates"
            if t.exists():
                count += len(list(t.glob("*.md")))
        self.assertEqual(count, 10)

    def test_main_skill_drives_agent_governance_instead_of_fixed_pipeline(self):
        text = (REPO / "skills" / "flowguard" / "SKILL.md").read_text(encoding="utf-8")
        for expected in ("智能体执行循环", "Spec Kit", "OpenSpec", "Superpowers", "context bind"):
            self.assertIn(expected, text)
        self.assertNotIn("把研发流程意图路由到正确的阶段技能", text)

    def test_stage_skills_are_explicit_legacy_compatibility_only(self):
        text = (REPO / "skills" / "flowguard-requirements" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("兼容模式", text)
        self.assertIn("仅当项目已有旧 `.flowguard` 十阶段状态", text)

if __name__ == "__main__":
    unittest.main()
