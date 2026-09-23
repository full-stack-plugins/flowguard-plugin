"""十阶段文档事实源的行为测试。

每个测试都针对一种可观察回归：项目目录污染、缓存丢失后状态丢失、
阶段越过、证据过期或迁移覆盖。
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from flowguard_lib import context, evidence, governance  # noqa: E402


class DocsPipelineTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.runtime = Path(tempfile.mkdtemp())
        self.previous_state_home = os.environ.get("FLOWGUARD_STATE_HOME")
        os.environ["FLOWGUARD_STATE_HOME"] = str(self.runtime)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "flowguard@example.test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "FlowGuard Test"], cwd=self.root, check=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/app.py"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.root, check=True)

    def tearDown(self):
        if self.previous_state_home is None:
            os.environ.pop("FLOWGUARD_STATE_HOME", None)
        else:
            os.environ["FLOWGUARD_STATE_HOME"] = self.previous_state_home
        shutil.rmtree(self.root)
        shutil.rmtree(self.runtime, ignore_errors=True)

    def bind(self, task_id="refund", parent_id=None):
        return context.bind(
            self.root, session_id="s", task_id=task_id,
            task_type="important_change", spec_system="external",
            spec_ref="https://example.test/spec/refund",
            parent_id=parent_id,
        )

    def test_binding_creates_ten_docs_without_project_private_state_directory(self):
        ctx = self.bind()

        self.assertFalse((self.root / ".flowguard").exists())
        from flowguard_lib import stage_docs
        self.assertEqual(len(stage_docs.snapshot(self.root, "refund")["stages"]), 10)
        self.assertTrue((self.root / "docs/project/02-architecture.md").is_file())
        self.assertTrue((self.root / "docs/features/refund/01-requirements.md").is_file())
        self.assertEqual(stage_docs.snapshot(self.root, "refund")["context"]["task_id"], ctx["task_id"])

    def test_binding_creation_failure_does_not_leave_partial_stage_document(self):
        target = self.root / "docs/features/refund/01-requirements.md"
        with mock.patch("os.link", side_effect=OSError("link failed")):
            with self.assertRaises(OSError):
                self.bind()
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.glob(".fg-atomic-*")), [])
        self.assertIsNone(context.active(self.root, "s"))

    def test_project_init_creation_failure_does_not_leave_partial_document(self):
        from flowguard_lib import stage_docs
        target = self.root / "docs/project/02-architecture.md"
        with mock.patch("os.link", side_effect=OSError("link failed")):
            with self.assertRaises(OSError):
                stage_docs.ensure_project(self.root)
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.glob(".fg-atomic-*")), [])

    def test_project_init_cannot_create_docs_while_state_lock_is_held(self):
        from flowguard_lib import state
        target = self.root / "docs/project/02-architecture.md"
        with state.state_lock(self.root):
            result = subprocess.run(
                [sys.executable, str(REPO / "scripts/flowguard_state.py"), "init", "--json"],
                cwd=self.root, capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(target.exists())

    def test_stage_advance_cannot_write_while_evidence_state_lock_is_held(self):
        self.bind()
        from flowguard_lib import stage_docs, state
        path = stage_docs.path_for(self.root, "refund", "01-requirements")
        before = path.read_bytes()

        with state.state_lock(self.root):
            result = subprocess.run(
                [sys.executable, str(REPO / "scripts/flowguard_state.py"),
                 "stage", "advance", "--task-id", "refund",
                 "--stage", "01-requirements", "--status", "in_progress", "--json"],
                cwd=self.root, capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(path.read_bytes(), before)

    def test_failed_stage_replace_preserves_existing_document(self):
        self.bind()
        from flowguard_lib import stage_docs
        path = stage_docs.path_for(self.root, "refund", "01-requirements")
        before = path.read_bytes()
        with mock.patch("os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                stage_docs.advance(self.root, "refund", "01-requirements", "in_progress")
        self.assertEqual(path.read_bytes(), before)

    def test_failed_evidence_replace_preserves_existing_document(self):
        ctx = self.bind()
        from flowguard_lib import stage_docs
        path = stage_docs.path_for(self.root, "refund", "04-testcases")
        before = path.read_bytes()
        with mock.patch("os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                evidence.record(
                    self.root, ctx["context_id"], kind="tests", producer="test",
                    result="fail", summary="suite failed", source_ref="test-run:1",
                )
        self.assertEqual(path.read_bytes(), before)

    def test_stage_and_evidence_update_preserve_document_permissions(self):
        ctx = self.bind()
        from flowguard_lib import stage_docs
        stage_path = stage_docs.path_for(self.root, "refund", "01-requirements")
        evidence_path = stage_docs.path_for(self.root, "refund", "04-testcases")
        for path in (stage_path, evidence_path):
            path.chmod(0o640)

        stage_docs.advance(self.root, "refund", "01-requirements", "in_progress")
        evidence.record(
            self.root, ctx["context_id"], kind="tests", producer="test",
            result="fail", summary="suite failed", source_ref="test-run:2",
        )

        self.assertEqual(stat.S_IMODE(stage_path.stat().st_mode), 0o640)
        self.assertEqual(stat.S_IMODE(evidence_path.stat().st_mode), 0o640)

    def test_docs_recover_stage_and_parent_after_runtime_cache_is_removed(self):
        parent = self.bind()
        self.bind("refund-callback", parent_id=parent["context_id"])
        shutil.rmtree(self.runtime)

        from flowguard_lib import stage_docs
        recovered = stage_docs.snapshot(self.root, "refund-callback")
        self.assertEqual(recovered["context"]["parent_task_id"], "refund")
        self.assertEqual(recovered["stages"]["01-requirements"]["status"], "pending")

    def test_session_start_lists_recoverable_docs_tasks_after_cache_loss(self):
        parent = self.bind()
        self.bind("refund-callback", parent_id=parent["context_id"])
        shutil.rmtree(self.runtime)

        result = subprocess.run(
            [sys.executable, str(REPO / "hooks/flowguard_status_summary.py")],
            input=json.dumps({"cwd": str(self.root), "session_id": "new-session"}),
            text=True, capture_output=True, cwd=self.root,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("可恢复任务", result.stdout)
        self.assertIn("refund-callback", result.stdout)
        self.assertIn("parent=refund", result.stdout)
        self.assertIn("项目阶段", result.stdout)
        self.assertFalse((self.root / ".flowguard").exists())

    def test_code_and_commit_wait_for_stage_documents_and_evidence(self):
        ctx = self.bind()
        context.approve(self.root, ctx["context_id"], "scope_approved", actor="user")
        from flowguard_lib import stage_docs
        denied = governance.evaluate(self.root, "code_write", session_id="s")
        self.assertFalse(denied["allowed"])
        self.assertIn("01-requirements", denied["envelope"]["missing"])

        (self.root / "tests").mkdir()
        (self.root / "tests/test_refund.py").write_text("def test_refund():\n    assert True\n", encoding="utf-8")
        for path in (self.root / "docs").rglob("*.md"):
            text = re.sub(r"\{\{[^}\n]+\}\}", "已确认", path.read_text(encoding="utf-8")).replace("状态: 已确认", "状态: accepted")
            text = text.replace("测试文件: 已确认", "测试文件: tests/test_refund.py")
            text = text.replace("- 结论: fix|wontfix|deferred", "- 结论: fix")
            path.write_text(text, encoding="utf-8")

        for stage in ("01-requirements", "02-architecture", "03-solution",
                      "04-testcases", "05-hld", "06-lld", "07-standards"):
            stage_docs.advance(self.root, "refund", stage, "accepted", approval_ref=f"user-receipt:{stage}")

        self.assertTrue(governance.evaluate(self.root, "code_write", session_id="s")["allowed"])
        for kind in ("tests", "static_analysis", "semantic_review"):
            evidence.record(
                self.root, ctx["context_id"], kind=kind, producer="fixture",
                result="pass", summary="passed", source_ref=f"ci:{kind}",
            )
        denied = governance.evaluate(self.root, "git_commit", session_id="s")
        self.assertEqual(denied["envelope"]["missing"], ["08-review", "09-docs"])
        for stage in ("08-review", "09-docs"):
            stage_docs.advance(self.root, "refund", stage, "accepted", approval_ref=f"user-receipt:{stage}")
        self.assertTrue(governance.evaluate(self.root, "git_commit", session_id="s")["allowed"])

    def test_release_acceptance_invalidates_when_listed_feature_docs_change(self):
        self.bind()
        from flowguard_lib import stage_docs
        (self.root / "tests").mkdir()
        (self.root / "tests/test_refund.py").write_text("def test_refund():\n    assert True\n", encoding="utf-8")
        release = stage_docs.path_for(self.root, "refund", "10-release")
        release.write_text(
            release.read_text(encoding="utf-8").replace(
                "| {{feature-id}} | {{✅ 已实现}} | {{...}} |",
                "| refund | ✅ 已实现 | 本次交付 |",
            ),
            encoding="utf-8",
        )
        for path in (self.root / "docs").rglob("*.md"):
            text = re.sub(r"\{\{[^}\n]+\}\}", "已确认", path.read_text(encoding="utf-8")).replace("状态: 已确认", "状态: accepted")
            text = text.replace("测试文件: 已确认", "测试文件: tests/test_refund.py")
            text = text.replace("- 结论: fix|wontfix|deferred", "- 结论: fix")
            path.write_text(text, encoding="utf-8")
        for stage in stage_docs.registry.ARTIFACTS:
            stage_docs.advance(self.root, "refund", stage, "accepted", approval_ref=f"user-receipt:{stage}")
        self.assertEqual(stage_docs.read(self.root, "refund", "10-release")["status"], "accepted")

        docs = stage_docs.path_for(self.root, "refund", "09-docs")
        docs.write_text(docs.read_text(encoding="utf-8") + "\n新的交付说明。\n", encoding="utf-8")
        self.assertEqual(stage_docs.read(self.root, "refund", "10-release")["status"], "invalidated")
        self.assertIn("10-release", stage_docs.missing_before(self.root, "refund", "release"))

    def test_release_scope_tracks_every_feature_with_escaped_table_text(self):
        self.bind()
        self.bind("refund-callback")
        from flowguard_lib import stage_docs
        (self.root / "tests").mkdir()
        (self.root / "tests/test_refund.py").write_text("def test_refund():\n    assert True\n", encoding="utf-8")
        release = stage_docs.path_for(self.root, "refund", "10-release")
        release.write_text(
            release.read_text(encoding="utf-8").replace(
                "| {{feature-id}} | {{✅ 已实现}} | {{...}} |",
                "| refund | ✅ 已实现 | 主流程 |\n"
                "| refund-callback | ✅ 已实现 | 回调 \\| 重试 |",
            ),
            encoding="utf-8",
        )
        for path in (self.root / "docs").rglob("*.md"):
            text = re.sub(r"\{\{[^}\n]+\}\}", "已确认", path.read_text(encoding="utf-8")).replace("状态: 已确认", "状态: accepted")
            text = text.replace("测试文件: 已确认", "测试文件: tests/test_refund.py")
            text = text.replace("- 结论: fix|wontfix|deferred", "- 结论: fix")
            path.write_text(text, encoding="utf-8")
        for stage in list(stage_docs.registry.ARTIFACTS)[:9]:
            stage_docs.advance(self.root, "refund", stage, "accepted", approval_ref=f"user-receipt:{stage}")
        for stage in ("01-requirements", "03-solution", "04-testcases", "05-hld",
                      "06-lld", "08-review", "09-docs"):
            stage_docs.advance(
                self.root, "refund-callback", stage, "accepted",
                approval_ref=f"user-receipt:{stage}",
            )
        try:
            stage_docs.advance(self.root, "refund", "10-release", "accepted", approval_ref="user-receipt:release")
        except stage_docs.StageDocError as error:
            self.fail(f"包含转义竖线的合法发布表格被拒绝: {error}")
        self.assertEqual(stage_docs.read(self.root, "refund", "10-release")["status"], "accepted")

        docs = stage_docs.path_for(self.root, "refund-callback", "09-docs")
        docs.write_text(docs.read_text(encoding="utf-8") + "\n回调重试说明更新。\n", encoding="utf-8")
        self.assertEqual(stage_docs.read(self.root, "refund", "10-release")["status"], "invalidated")

    def test_evidence_is_in_document_and_code_change_invalidates_it(self):
        ctx = self.bind()
        evidence.record(
            self.root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="144 tests", source_ref="ci:42",
        )

        text = (self.root / "docs/features/refund/04-testcases.md").read_text(encoding="utf-8")
        self.assertIn("ci:42", text)
        self.assertIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))
        (self.root / "src/app.py").write_text("print('v2')\n", encoding="utf-8")
        self.assertNotIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))
        self.assertFalse((self.root / ".flowguard").exists())

    def test_user_release_acceptance_expires_when_code_changes(self):
        ctx = self.bind()
        item = evidence.record(
            self.root, ctx["context_id"], kind="user_acceptance", producer="user",
            result="pass", summary="release accepted", source_ref="approval:1",
        )
        self.assertTrue(item["expires_on_change"])
        self.assertIn("user_acceptance", evidence.valid_kinds(self.root, ctx["context_id"]))

        (self.root / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
        self.assertNotIn("user_acceptance", evidence.valid_kinds(self.root, ctx["context_id"]))

    def test_gate_evidence_cannot_disable_code_change_expiry(self):
        ctx = self.bind()
        with self.assertRaisesRegex(evidence.EvidenceError, "不能关闭"):
            evidence.record(
                self.root, ctx["context_id"], kind="tests", producer="agent",
                result="pass", summary="claimed pass", source_ref="claim:1",
                expires_on_change=False,
            )

    def test_legacy_non_expiring_gate_row_does_not_survive_code_change(self):
        ctx = self.bind()
        evidence.record(
            self.root, ctx["context_id"], kind="tests", producer="legacy",
            result="pass", summary="old pass", source_ref="legacy:1",
        )
        path = self.root / "docs/features/refund/04-testcases.md"
        original = path.read_text(encoding="utf-8")
        self.assertIn("| True | active |", original)
        path.write_text(original.replace("| True | active |", "| False | active |"), encoding="utf-8")

        (self.root / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
        self.assertNotIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))

    def test_evidence_from_one_session_does_not_approve_another_context(self):
        first = self.bind()
        second = context.bind(
            self.root, session_id="other-session", task_id="refund",
            task_type="important_change", spec_system="external",
            spec_ref="https://example.test/spec/refund",
        )
        self.assertNotEqual(first["context_id"], second["context_id"])
        evidence.record(
            self.root, first["context_id"], kind="tests", producer="unittest",
            result="pass", summary="first session passed", source_ref="run:1",
        )

        self.assertIn("tests", evidence.valid_kinds(self.root, first["context_id"]))
        self.assertNotIn("tests", evidence.valid_kinds(self.root, second["context_id"]))

    def test_old_evidence_row_without_context_id_is_not_gate_evidence(self):
        ctx = self.bind()
        evidence.record(
            self.root, ctx["context_id"], kind="tests", producer="legacy",
            result="pass", summary="old pass", source_ref="legacy:1",
        )
        path = self.root / "docs/features/refund/04-testcases.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("| ID | 上下文 | 类型 |", "| ID | 类型 |")
        text = text.replace(f" | {ctx['context_id']} | tests |", " | tests |")
        path.write_text(text, encoding="utf-8")

        self.assertNotIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))

    def test_appending_evidence_upgrades_legacy_table_header(self):
        ctx = self.bind()
        evidence.record(
            self.root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="first run", source_ref="run:1",
        )
        path = self.root / "docs/features/refund/04-testcases.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("| ID | 上下文 | 类型 |", "| ID | 类型 |")
        text = text.replace("|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|",
                            "|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|")
        path.write_text(text, encoding="utf-8")

        evidence.record(
            self.root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="second run", source_ref="run:2",
        )
        self.assertIn("| ID | 上下文 | 类型 |", path.read_text(encoding="utf-8"))

    def test_native_superpowers_spec_change_invalidates_verification_evidence(self):
        spec = self.root / "docs/superpowers/specs/refund.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Refund v1\n", encoding="utf-8")
        ctx = context.bind(
            self.root, session_id="s", task_id="refund",
            task_type="important_change", spec_system="superpowers",
            spec_ref="docs/superpowers/specs/refund.md",
        )
        evidence.record(self.root, ctx["context_id"], kind="tests", producer="unittest",
                        result="pass", summary="passed", source_ref="ci:1")
        self.assertIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))
        spec.write_text("# Refund v2\n", encoding="utf-8")
        self.assertNotIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))

    def test_current_task_requirement_body_change_invalidates_verification_evidence(self):
        ctx = self.bind()
        evidence.record(self.root, ctx["context_id"], kind="tests", producer="unittest",
                        result="pass", summary="passed", source_ref="ci:1")
        self.assertIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))

        requirement = self.root / "docs/features/refund/01-requirements.md"
        requirement.write_text(requirement.read_text(encoding="utf-8") + "\n新增验收规则：重复退款不可扣款。\n",
                               encoding="utf-8")
        self.assertNotIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))

    def test_parent_requirement_body_change_invalidates_child_verification_evidence(self):
        parent = self.bind("refund")
        child = self.bind("refund-callback", parent_id=parent["context_id"])
        evidence.record(self.root, child["context_id"], kind="tests", producer="unittest",
                        result="pass", summary="passed", source_ref="ci:child")
        self.assertIn("tests", evidence.valid_kinds(self.root, child["context_id"]))

        requirement = self.root / "docs/features/refund/01-requirements.md"
        requirement.write_text(requirement.read_text(encoding="utf-8") + "\n父级新增约束：回调需幂等。\n",
                               encoding="utf-8")
        self.assertNotIn("tests", evidence.valid_kinds(self.root, child["context_id"]))

    def test_rebinding_to_a_different_formal_spec_invalidates_old_evidence(self):
        ctx = self.bind()
        evidence.record(self.root, ctx["context_id"], kind="tests", producer="unittest",
                        result="pass", summary="passed", source_ref="ci:old-spec")
        self.assertIn("tests", evidence.valid_kinds(self.root, ctx["context_id"]))

        rebound = context.bind(
            self.root, session_id="s", task_id="refund", task_type="important_change",
            spec_system="external", spec_ref="https://example.test/spec/refund-v2",
        )
        self.assertEqual(rebound["context_id"], ctx["context_id"])
        self.assertNotIn("tests", evidence.valid_kinds(self.root, rebound["context_id"]))

    def test_latest_failure_in_docs_overrides_old_pass(self):
        ctx = self.bind()
        for result in ("pass", "fail"):
            evidence.record(
                self.root, ctx["context_id"], kind="static_analysis",
                producer="codeguard", result=result, summary=result,
                source_ref=f"ci:{result}",
            )
        self.assertNotIn("static_analysis", evidence.valid_kinds(self.root, ctx["context_id"]))
        self.assertIn("ci:fail", (self.root / "docs/features/refund/08-review.md").read_text(encoding="utf-8"))

    def test_generated_placeholder_document_cannot_be_accepted(self):
        self.bind()
        from flowguard_lib import stage_docs

        with self.assertRaisesRegex(stage_docs.StageDocError, "占位符"):
            stage_docs.advance(
                self.root, "refund", "01-requirements", "accepted",
                approval_ref="user-receipt:1",
            )
        self.assertEqual(stage_docs.read(self.root, "refund", "01-requirements")["status"], "pending")

    def test_reason_text_alone_cannot_mark_stage_accepted_or_skipped(self):
        self.bind()
        from flowguard_lib import stage_docs
        for target in ("accepted", "skipped"):
            with self.subTest(target=target):
                with self.assertRaisesRegex(stage_docs.StageDocError, "批准依据"):
                    stage_docs.advance(self.root, "refund", "01-requirements", target,
                                       reason="agent-says-approved")

    def test_editing_accepted_stage_invalidates_its_document_fingerprint(self):
        self.bind()
        from flowguard_lib import stage_docs
        path = self.root / "docs/features/refund/01-requirements.md"
        text = re.sub(r"\{\{[^}\n]+\}\}", "已确认", path.read_text(encoding="utf-8")).replace("状态: 已确认", "状态: accepted")
        path.write_text(text, encoding="utf-8")
        stage_docs.advance(self.root, "refund", "01-requirements", "accepted", approval_ref="user-receipt:1")

        path.write_text(path.read_text(encoding="utf-8") + "\n新增加的业务条件。\n", encoding="utf-8")
        self.assertEqual(stage_docs.read(self.root, "refund", "01-requirements")["status"], "invalidated")

    def test_reaccepting_changed_requirement_does_not_silently_reuse_downstream_acceptance(self):
        self.bind()
        from flowguard_lib import stage_docs
        for stage in ("01-requirements", "02-architecture", "03-solution"):
            path = stage_docs.path_for(self.root, "refund", stage)
            path.write_text(re.sub(r"\{\{[^}\n]+\}\}", "已确认", path.read_text(encoding="utf-8")).replace("状态: 已确认", "状态: accepted"),
                            encoding="utf-8")
            stage_docs.advance(self.root, "refund", stage, "accepted", approval_ref=f"user:{stage}")
        requirement = stage_docs.path_for(self.root, "refund", "01-requirements")
        requirement.write_text(requirement.read_text(encoding="utf-8") + "\n新业务条件。\n", encoding="utf-8")
        self.assertEqual(stage_docs.read(self.root, "refund", "03-solution")["status"], "invalidated")
        stage_docs.advance(self.root, "refund", "01-requirements", "accepted", approval_ref="user:recheck")
        self.assertEqual(stage_docs.read(self.root, "refund", "03-solution")["status"], "invalidated")


if __name__ == "__main__":
    unittest.main()
