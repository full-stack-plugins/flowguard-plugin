import tempfile, unittest
from pathlib import Path
from scripts.flowguard_lib import validation

GOOD_REQ = """\
# 需求分析

### Requirement: 订单退款申请
`order-refund/REQ-1` 用户 SHALL 能对已完成订单发起退款申请。

#### Scenario: 正常退款申请
- **WHEN** 用户提交退款
- **THEN** 生成退款单

### Requirement: 退款审核
`order-refund/REQ-2` 审核 SHALL 在 24h 内完成。
"""

class RequirementsTest(unittest.TestCase):
    def test_good_no_issues(self):
        issues = validation.validate_requirements(GOOD_REQ, "order-refund")
        self.assertEqual([i for i in issues if i["level"] == "ERROR"], [], issues)

    def test_requirement_ids(self):
        self.assertEqual(validation.requirement_ids(GOOD_REQ),
                         ["order-refund/REQ-1", "order-refund/REQ-2"])

    def test_missing_shall(self):
        bad = GOOD_REQ.replace("SHALL", "可以")
        issues = validation.validate_requirements(bad, "order-refund")
        self.assertTrue(any("SHALL" in i["message"] or "MUST" in i["message"] for i in issues))

    def test_missing_scenario_is_warning(self):
        bad = GOOD_REQ.split("#### Scenario")[0] + "`order-refund/REQ-1` 尾部"
        issues = validation.validate_requirements(bad + "\n", "order-refund")
        self.assertTrue(any(i["level"] == "WARNING" and "Scenario" in i["message"] for i in issues))

    def test_wrong_feature_id(self):
        bad = GOOD_REQ.replace("order-refund/REQ-1", "other-feature/REQ-1")
        issues = validation.validate_requirements(bad, "order-refund")
        self.assertTrue(any(i["level"] == "ERROR" and "REQ" in i["message"] for i in issues))

    def test_stray_scenario_header(self):
        bad = GOOD_REQ + "\n### Scenario: 三级标题\n"
        issues = validation.validate_requirements(bad, "order-refund")
        self.assertTrue(any(i["level"] == "ERROR" and "####" in i["fix"] for i in issues))

    def test_code_fence_masked(self):
        fenced = GOOD_REQ + "\n```\n### Requirement: 围栏内不算\n```\n"
        self.assertEqual(validation.requirement_ids(fenced),
                         ["order-refund/REQ-1", "order-refund/REQ-2"])

class TestcasesTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_covered_and_file_exists(self):
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_refund.py").write_text("x")
        tc = """\
### 用例 TC-1: 正常退款
- REQ: order-refund/REQ-1
- 测试文件: tests/test_refund.py
"""
        issues = validation.validate_testcases(tc, ["order-refund/REQ-1"], root=self.root)
        self.assertEqual(issues, [])

    def test_missing_coverage(self):
        tc = "### 用例 TC-1: 名称\n- REQ: order-refund/REQ-1\n- 测试文件: tests/t.py\n"
        issues = validation.validate_testcases(tc, ["order-refund/REQ-1", "order-refund/REQ-2"], root=self.root)
        self.assertTrue(any("REQ-2" in i["message"] for i in issues))

    def test_missing_test_file(self):
        tc = "### 用例 TC-1: 名称\n- REQ: order-refund/REQ-1\n- 测试文件: tests/nope.py\n"
        issues = validation.validate_testcases(tc, ["order-refund/REQ-1"], root=self.root)
        self.assertTrue(any(i["level"] == "ERROR" and "测试文件" in i["message"] for i in issues))

class ReviewTest(unittest.TestCase):
    def test_all_concluded(self):
        rv = "### 发现: 空指针风险\n- 证据: A.java:12\n- 结论: fix\n"
        self.assertEqual(validation.validate_review(rv), [])

    def test_unconcluded(self):
        rv = "### 发现: 空指针风险\n- 证据: A.java:12\n### 发现: 命名\n- 结论: wontfix\n"
        issues = validation.validate_review(rv)
        self.assertEqual(len(issues), 1)
        self.assertIn("结论", issues[0]["message"])

class Tier2Test(unittest.TestCase):
    def test_missing_reports_install_cmd(self):
        refs = [("ghost-skill", "ghost-pkg", "npx skills add full-stack-skills/ghost-pkg --skill ghost-skill")]
        out = validation.missing_tier2(refs, root=Path(tempfile.mkdtemp()))
        self.assertEqual(len(out), 1)
        self.assertIn("npx skills add", out[0]["fix"])

    def test_installed_in_root_agents(self):
        root = Path(tempfile.mkdtemp())
        (root / ".agents" / "skills" / "local-skill").mkdir(parents=True)
        (root / ".agents" / "skills" / "local-skill" / "SKILL.md").write_text("x")
        refs = [("local-skill", "p", "cmd")]
        self.assertEqual(validation.missing_tier2(refs, root=root), [])


class ProjectDocValidationTest(unittest.TestCase):
    def test_architecture_template_and_valid_adr_pass(self):
        self.assertEqual(validation.validate_architecture(
            "- ADR-{{编号}} | feature: {{来源}} | 状态: {{proposed/accepted}} —— {{决策}}"), [])
        self.assertEqual(validation.validate_architecture(
            "- ADR-0001 | feature: refund | 状态: accepted —— 采用追加式 ADR"), [])

    def test_architecture_adr_missing_feature_or_status_is_error(self):
        issues = validation.validate_architecture(
            "- ADR-0002 | 状态: accepted —— 缺来源\n- ADR-0003 | feature: refund | 状态: draft —— 非法状态")
        self.assertEqual([i["level"] for i in issues], ["ERROR", "ERROR"])
        self.assertTrue(any("feature" in i["message"] for i in issues))
        self.assertTrue(any("状态" in i["message"] for i in issues))

    def test_standards_template_vacuous_and_coverage(self):
        self.assertEqual(validation.validate_standards(
            "## 2. 规范集\n\n### 2.1 {{模块 / 栈名}}\n- {{条目}}\n\n## 3. 增补\n",
            {"order": {"stack": "java-spring"}}), [])
        covered = "## 2. 规范集 (Standards)\n\n### 2.1 order / java-spring\n- 规约条目\n\n## 3. 增补\n"
        self.assertEqual(validation.validate_standards(covered,
                                                       {"order": {"stack": "java-spring"}}), [])
        issues = validation.validate_standards(covered,
                                               {"order": {"stack": "java-spring"},
                                                "web": {"stack": "vue3"}})
        self.assertEqual([i["level"] for i in issues], ["ERROR"])
        self.assertIn("web", issues[0]["message"])
        # 无栈模块（无法判定技术栈）跳过
        self.assertEqual(validation.validate_standards(covered, {"app": {"stack": None}}), [])

    def test_release_template_vacuous_and_unknown_feature(self):
        self.assertEqual(validation.validate_release(
            "## 3. 发布内容\n\n| {{feature-id}} | {{✅ 已实现}} | {{...}} |\n\n## 4. 校验\n",
            ["refund"]), [])
        body = ("## 3. 发布内容 (Scope)\n\n"
                "| 功能 (feature) | 状态 | 说明 |\n| :--- | :--- | :--- |\n"
                "| refund | ✅ | ok |\n| ghost | ✅ | 幽灵 |\n\n## 4. 校验\n")
        issues = validation.validate_release(body, ["refund"])
        self.assertEqual([i["level"] for i in issues], ["ERROR"])
        self.assertIn("ghost", issues[0]["message"])

    def test_known_task_ids(self):
        root = Path(tempfile.mkdtemp())
        (root / "docs" / "features" / "refund").mkdir(parents=True)
        (root / "docs" / "features" / "Bad_ID").mkdir(parents=True)
        self.assertEqual(validation.known_task_ids(root), ["refund"])

if __name__ == "__main__":
    unittest.main()
