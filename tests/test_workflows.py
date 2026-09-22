import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

class WorkflowsTest(unittest.TestCase):
    def test_skills_check_required_steps(self):
        t = (REPO / ".github" / "workflows" / "skills-check.yml").read_text(encoding="utf-8")
        self.assertIn("skill_vendor.py check --offline", t)
        self.assertIn("unittest discover", t)
        self.assertIn("generate_skills.py", t)
        self.assertIn("git diff --exit-code skills/", t)

    def test_skills_sync_triggers(self):
        t = (REPO / ".github" / "workflows" / "skills-sync.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", t)
        self.assertIn("repository_dispatch", t)
        self.assertIn("cron:", t)
        self.assertIn("skill_vendor.py update", t)

if __name__ == "__main__":
    unittest.main()
