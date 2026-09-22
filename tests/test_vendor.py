import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VENDOR = REPO / "scripts" / "vendor" / "skill_vendor.py"

class VendorTest(unittest.TestCase):
    def test_check_offline_clean_tree(self):
        p = subprocess.run([sys.executable, str(VENDOR), "check", "--offline"],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_local_whitelist_covers_all_skills(self):
        whitelist = set(json.loads((REPO / "plugin-local-skills.json").read_text(encoding="utf-8"))["skills"])
        actual = {d.name for d in (REPO / "skills").iterdir() if d.is_dir()}
        self.assertEqual(actual, whitelist)

    def test_undeclared_dir_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            shutil.copytree(REPO / "skills", td / "skills")
            shutil.copy(REPO / "skills.lock.json", td / "skills.lock.json")
            shutil.copy(REPO / "plugin-local-skills.json", td / "plugin-local-skills.json")
            (td / "skills" / "rogue-skill").mkdir()
            (td / "skills" / "rogue-skill" / "SKILL.md").write_text("x")
            p = subprocess.run([sys.executable, str(VENDOR), "check", "--offline"],
                               cwd=td, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            combined = p.stdout + p.stderr
            self.assertIn("rogue-skill", combined)

if __name__ == "__main__":
    unittest.main()
