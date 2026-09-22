import re, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

class LinkDisciplineTest(unittest.TestCase):
    """AGENTS.md 纪律：SKILL/命令内禁止跨技能相对路径（../）。"""

    def test_no_cross_skill_relative_links(self):
        bad = []
        for md in (REPO / "skills").rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            for m in re.finditer(r"\]\((\.\.?/[^)]+)\)", text):
                bad.append(f"{md}: {m.group(1)}")
        self.assertEqual(bad, [])

    def test_readmes_exist(self):
        for f in ("README.md", "README.zh-CN.md", "AGENTS.md", "docs/architecture.md",
                  "PRIVACY.md", "TERMS.md", "THIRD-PARTY-NOTICES.md", "LICENSE"):
            self.assertTrue((REPO / f).exists(), f)

if __name__ == "__main__":
    unittest.main()
