import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "scripts" / "flowguard_state.py"


def run(root, *argv):
    return subprocess.run([sys.executable, str(CLI), *argv], cwd=root,
                          capture_output=True, text=True)


class ValidateCliTest(unittest.TestCase):
    """validate 面向 docs/features/<task-id>/：内容校验、追溯矩阵与 Tier2 检查。"""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.task = "order-refund"
        bound = run(self.root, "context", "bind", "--session", "s", "--task-id", self.task,
                    "--task-type", "simple_change", "--spec-system", "none", "--json")
        self.assertEqual(bound.returncode, 0, bound.stderr)

    def test_template_state_passes_with_tier2_warning_only(self):
        r = run(self.root, "validate", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertTrue(out["ok"])
        self.assertTrue(all(i["level"] != "ERROR" for i in out["issues"]))

    def test_wrong_feature_req_id_is_error(self):
        path = self.root / "docs" / "features" / self.task / "01-requirements.md"
        path.write_text(
            "### 1.3 FlowGuard 阶段信息\n\n"
            "| 字段 | 值 |\n|:---|:---|\n"
            f"| 任务 | {self.task} |\n| 父任务 | - |\n| 阶段 | 01-requirements |\n"
            "| 阶段状态 | pending |\n| 规格事实源 | none |\n| 原生产物 | - |\n"
            "| 批准依据 | - |\n| 前置指纹 | - |\n| 验收指纹 | - |\n\n"
            "## 3. 用户故事与验收标准\n\n"
            "### Requirement: 退款接口\n`other/REQ-1` SHALL 提供退款。\n\n#### Scenario: 成功\n",
            encoding="utf-8")
        r = run(self.root, "validate", "--json")
        self.assertEqual(r.returncode, 3)
        out = json.loads(r.stdout)
        self.assertFalse(out["ok"])
        self.assertTrue(any("other/REQ-1" in i["message"] for i in out["issues"]))

    def test_task_id_filter_and_unknown_task(self):
        ok = run(self.root, "validate", "--task-id", self.task, "--json")
        self.assertEqual(ok.returncode, 0, ok.stdout)
        missing = run(self.root, "validate", "--task-id", "nope", "--json")
        self.assertEqual(missing.returncode, 3)
        self.assertEqual(json.loads(missing.stdout)["code"], "unknown_task")
        self.assertFalse((self.root / ".flowguard").exists())


if __name__ == "__main__":
    unittest.main()
