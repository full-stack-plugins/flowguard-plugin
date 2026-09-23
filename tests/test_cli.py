import json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "scripts" / "flowguard_state.py"


def run(root, *argv):
    return subprocess.run([sys.executable, str(CLI), *argv], cwd=root,
                          capture_output=True, text=True)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "pom.xml").write_text("<project/>", encoding="utf-8")
        (self.root / ".flowguard").mkdir()  # 显式旧项目夹具

    def test_full_walk(self):
        # init 幂等
        r = run(self.root, "legacy-init", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["modules"], ["app"])
        self.assertEqual(run(self.root, "legacy-init").returncode, 0)

        # 功能创建 + 非法 id
        r = run(self.root, "feature", "new", "order-refund", "--modules", "app", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run(self.root, "feature", "new", "Bad_ID", "--modules", "app")
        self.assertEqual(r.returncode, 3)
        r = run(self.root, "feature", "new", "order-refund", "--modules", "app")
        self.assertEqual(r.returncode, 3)

        # 未开始阶段：写码被门禁拒绝（exit 2，信封 code）
        r = run(self.root, "gate", "--action", "write_code", "--path", "app/A.java", "--json")
        self.assertEqual(r.returncode, 2)
        self.assertIn("gate_write_code", r.stdout)

        # 五个功能级阶段 next → advance（advance = 用户验收）
        for _ in range(5):
            self.assertEqual(run(self.root, "next", "--json").returncode, 0)
            r = run(self.root, "advance", "--evidence", "用户确认", "--json")
            self.assertEqual(r.returncode, 0, r.stderr)

        # 项目级规范阶段（advance 必须显式 --stage，否则默认作用于 current_feature）
        self.assertEqual(run(self.root, "next", "--stage", "standards", "--json").returncode, 0)
        r = run(self.root, "advance", "--stage", "standards", "--evidence", "用户确认", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)

        # 写码放行
        r = run(self.root, "gate", "--action", "write_code", "--path", "app/A.java", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        # 看板
        r = run(self.root, "status", "--json")
        self.assertEqual(r.returncode, 0)
        st = json.loads(r.stdout)
        self.assertEqual(st["features"]["order-refund"]["stages"]["requirements"], "accepted")
        self.assertEqual(st["current_feature"], "order-refund")

        # override 留痕（review 阶段还在 pending）
        r = run(self.root, "override", "--stage", "review", "--reason", "hotfix 需求", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)

        # validate：全模板态（示例块含占位符）→ 不参与机械检查，validate 通过
        r = run(self.root, "validate", "--json")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(json.loads(r.stdout)["ok"])

        # 未初始化目录：gate 放行
        empty = Path(tempfile.mkdtemp())
        r = run(empty, "gate", "--action", "write_code", "--path", "src/A.java", "--json")
        self.assertEqual(r.returncode, 0)

    def test_instructions_json(self):
        self.assertEqual(run(self.root, "legacy-init", "--json").returncode, 0)
        r = run(self.root, "instructions", "01-requirements", "--json")
        self.assertEqual(r.returncode, 0)
        ins = json.loads(r.stdout)
        for key in ("artifact", "scope", "stage", "context", "rules", "template", "requires", "unlocks", "tier2"):
            self.assertIn(key, ins)

if __name__ == "__main__":
    unittest.main()
