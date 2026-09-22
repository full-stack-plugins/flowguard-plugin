"""端到端验收：≥2 模块 × ≥2 功能，双功能交错推进到部署交付（spec §12 验收标准）。"""
import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "scripts" / "flowgate_state.py"
FIXTURE = REPO / "tests" / "fixtures" / "multi_feature"

REQ_A = """# 订单退款 —— 需求分析

### Requirement: 退款申请
`order-refund/REQ-1` 用户 SHALL 能对已完成订单发起退款申请。

#### Scenario: 正常申请
- **WHEN** 用户提交退款
- **THEN** 生成退款单
"""

TC_A = """# 订单退款 —— 测试用例

### 用例 TC-1: 正常退款
- REQ: order-refund/REQ-1
- 测试文件: tests/test_refund.py
- 步骤: 提交退款
- 预期: 生成退款单
"""


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(FIXTURE, self.root, dirs_exist_ok=True)

    def cli(self, *argv):
        p = subprocess.run([sys.executable, str(CLI), *argv], cwd=self.root,
                           capture_output=True, text=True)
        return p

    def advance(self, *extra):
        p = self.cli("advance", "--evidence", "用户确认", *extra, "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_two_features_two_modules_full_walk(self):
        # init：探测双模块
        r = self.cli("init", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        init = json.loads(r.stdout)
        self.assertEqual(sorted(init["modules"]), ["order", "web"])
        self.assertEqual(init["stack"]["backend"], "java-spring")
        self.assertEqual(init["stack"]["frontend"], "vue3")

        # 功能 A（跨双模块）+ 功能 B
        self.assertEqual(self.cli("feature", "new", "order-refund",
                                  "--modules", "order", "web", "--json").returncode, 0)
        self.assertEqual(self.cli("feature", "new", "user-export",
                                  "--modules", "web", "--json").returncode, 0)

        # 项目级：架构 + 规范
        self.assertEqual(self.cli("next", "--stage", "architecture").returncode, 0)
        self.advance("--stage", "architecture")
        self.assertEqual(self.cli("next", "--stage", "standards").returncode, 0)
        self.advance("--stage", "standards")

        # A：真实内容写入需求与用例（含测试文件），五阶段逐个验收
        adir = self.root / ".flowgate" / "features" / "order-refund" / "artifacts"
        (adir / "01-requirements.md").write_text(REQ_A, encoding="utf-8")
        (adir / "04-testcases.md").write_text(TC_A, encoding="utf-8")
        tests_dir = self.root / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "test_refund.py").write_text("def test_refund():\n    assert True\n", encoding="utf-8")
        for _ in range(5):
            self.assertEqual(self.cli("next", "--feature", "order-refund").returncode, 0)
            self.advance("--feature", "order-refund")

        # TDD 门槛生效：current=A，A 写码放行（含跨模块 web）
        r = self.cli("gate", "--action", "write_code", "--path", "server/order/A.java", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("gate", "--action", "write_code", "--path", "web/src/Pay.vue", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        # A：validate 全绿（REQ 覆盖 + 测试文件存在）
        r = self.cli("validate", "--feature", "order-refund", "--json")
        self.assertEqual(r.returncode, 0, r.stdout)

        # B：只推进了需求（in_progress）→ current 切到 B 后写码被 TDD 拒绝
        self.assertEqual(self.cli("next", "--feature", "user-export").returncode, 0)
        r = self.cli("gate", "--action", "write_code", "--path", "web/src/E.vue", "--json")
        self.assertEqual(r.returncode, 2)
        self.assertIn("gate_write_code_tdd", r.stdout)

        # A：审查 + 文档验收 → done
        self.assertEqual(self.cli("next", "--feature", "order-refund").returncode, 0)
        self.advance("--feature", "order-refund")   # review
        self.assertEqual(self.cli("next", "--feature", "order-refund").returncode, 0)
        self.advance("--feature", "order-refund")   # docs → done
        st = json.loads(self.cli("status", "--json").stdout)
        self.assertEqual(st["features"]["order-refund"]["status"], "done")

        # B：留痕放弃
        self.assertEqual(self.cli("feature", "drop", "user-export",
                                  "--reason", "需求撤销", "--json").returncode, 0)

        # 交付收口
        self.assertEqual(self.cli("next", "--stage", "release").returncode, 0)
        self.advance("--stage", "release")
        self.assertTrue((self.root / ".flowgate" / "project" / "10-release.md").exists())
        r = self.cli("gate", "--action", "build_release", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        # journal 全程留痕
        jl = (self.root / ".flowgate" / "journal" / "events.jsonl").read_text(encoding="utf-8")
        for ev in ("init", "feature_new", "accepted_by_user", "feature_drop"):
            self.assertIn(f'"event": "{ev}"', jl)

if __name__ == "__main__":
    unittest.main()
