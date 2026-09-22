import json, re, subprocess, sys, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "scripts" / "generate_skills.py"

class ParityTest(unittest.TestCase):
    def test_generated_skills_match_committed(self):
        r = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True, cwd=REPO)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = subprocess.run(["git", "diff", "--exit-code", "skills/"], cwd=REPO,
                           capture_output=True, text=True)
        self.assertEqual(d.returncode, 0,
                         "skills/ 与模板生成结果不一致：先运行 scripts/generate_skills.py 再提交\n" + d.stdout[:2000])

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

if __name__ == "__main__":
    unittest.main()
