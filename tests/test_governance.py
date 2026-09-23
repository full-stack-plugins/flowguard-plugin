import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from flowguard_lib import context, discovery, evidence, governance  # noqa: E402


def git_repo():
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "flowguard@example.test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "FlowGuard Test"], cwd=root, check=True)
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/app.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
    return root


class DiscoveryTest(unittest.TestCase):
    def test_git_project_without_sdd_requires_assessment_not_initialization(self):
        root = git_repo()

        result = discovery.discover(root)

        self.assertTrue(result["git"]["is_repository"])
        self.assertEqual(result["project_type"], "brownfield")
        self.assertIsNone(result["sdd"]["selected_system"])
        self.assertEqual(result["sdd"]["status"], "assessment_required")
        self.assertFalse((root / ".specify").exists())
        self.assertFalse((root / "openspec").exists())

    def test_native_openspec_is_selected_without_copying_artifacts(self):
        root = git_repo()
        change = root / "openspec" / "changes" / "refund-idempotency"
        change.mkdir(parents=True)
        (change / "proposal.md").write_text("# proposal\n", encoding="utf-8")

        result = discovery.discover(root)

        self.assertEqual(result["sdd"]["selected_system"], "openspec")
        self.assertEqual(result["sdd"]["status"], "ready")
        self.assertIn("openspec/changes/refund-idempotency", result["sdd"]["artifacts"])

    def test_spec_kit_and_openspec_conflict_requires_user_choice(self):
        root = git_repo()
        (root / ".specify" / "specs" / "001-login").mkdir(parents=True)
        (root / "openspec" / "changes" / "login").mkdir(parents=True)

        result = discovery.discover(root)

        self.assertEqual(result["sdd"]["status"], "choice_required")
        self.assertIsNone(result["sdd"]["selected_system"])
        self.assertIn("spec-kit", result["sdd"]["conflicts"])
        self.assertIn("openspec", result["sdd"]["conflicts"])


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.root = git_repo()
        self.spec = self.root / "openspec" / "changes" / "refund"
        self.spec.mkdir(parents=True)

    def test_active_context_is_scoped_by_session_and_worktree(self):
        first = context.bind(
            self.root, session_id="session-a", task_id="refund-api",
            task_type="important_change", spec_system="openspec",
            spec_ref="openspec/changes/refund",
        )
        second = context.bind(
            self.root, session_id="session-b", task_id="refund-ui",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )

        self.assertNotEqual(first["context_id"], second["context_id"])
        self.assertEqual(context.active(self.root, "session-a")["task_id"], "refund-api")
        self.assertEqual(context.active(self.root, "session-b")["task_id"], "refund-ui")

    def test_repository_root_cannot_be_bound_as_formal_spec(self):
        with self.assertRaisesRegex(context.ContextError, "规格引用不能是仓库根目录"):
            context.bind(
                self.root, session_id="s", task_id="refund",
                task_type="important_change", spec_system="openspec", spec_ref=".",
            )

    def test_parent_cannot_complete_before_required_child(self):
        parent = context.bind(
            self.root, session_id="s", task_id="refund",
            task_type="important_change", spec_system="openspec",
            spec_ref="openspec/changes/refund",
        )
        child = context.bind(
            self.root, session_id="s", task_id="refund-callback",
            task_type="important_change", spec_system="openspec",
            spec_ref="openspec/changes/refund", parent_id=parent["context_id"],
        )

        with self.assertRaisesRegex(context.ContextError, "子任务"):
            context.complete(self.root, parent["context_id"])
        context.complete(self.root, child["context_id"])
        completed = context.complete(self.root, parent["context_id"])
        self.assertEqual(completed["status"], "completed")

    def test_rebinding_same_task_preserves_unchanged_approvals(self):
        first = context.bind(
            self.root, session_id="s", task_id="refund",
            task_type="important_change", spec_system="openspec",
            spec_ref="openspec/changes/refund",
        )
        context.approve(self.root, first["context_id"], "scope_approved", actor="user")

        rebound = context.bind(
            self.root, session_id="s", task_id="refund",
            task_type="important_change", spec_system="openspec",
            spec_ref="openspec/changes/refund",
        )

        self.assertIn("scope_approved", rebound["approvals"])

    def test_dependency_cycle_is_rejected(self):
        first = context.bind(
            self.root, session_id="s", task_id="first",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        second = context.bind(
            self.root, session_id="s", task_id="second",
            task_type="simple_change", spec_system="none", spec_ref=None,
            depends_on=[first["context_id"]],
        )

        with self.assertRaisesRegex(context.ContextError, "依赖成环"):
            context.bind(
                self.root, session_id="s", task_id="first",
                task_type="simple_change", spec_system="none", spec_ref=None,
                depends_on=[second["context_id"]],
            )


class EvidenceTest(unittest.TestCase):
    def test_unborn_repository_ignores_gitignored_files_in_evidence_fingerprint(self):
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        ignored = root / "ignored.txt"
        ignored.write_text("first\n", encoding="utf-8")
        ctx = context.bind(
            root, session_id="s", task_id="small-fix",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        evidence.record(
            root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="passed", source_ref="run-1",
        )
        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

        ignored.write_text("second\n", encoding="utf-8")

        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

    def test_untracked_symlink_does_not_hash_external_target_contents(self):
        root = git_repo()
        outside = Path(tempfile.mkdtemp()) / "outside.txt"
        outside.write_text("first\n", encoding="utf-8")
        (root / "outside-link").symlink_to(outside)
        ctx = context.bind(
            root, session_id="s", task_id="small-fix",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        evidence.record(
            root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="passed", source_ref="run-1",
        )
        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

        outside.write_text("second\n", encoding="utf-8")

        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

    def test_unrelated_openspec_change_does_not_expire_bound_task_evidence(self):
        root = git_repo()
        refund = root / "openspec" / "changes" / "refund"
        other = root / "openspec" / "changes" / "other"
        refund.mkdir(parents=True)
        other.mkdir(parents=True)
        (refund / "proposal.md").write_text("# Refund\n", encoding="utf-8")
        (other / "proposal.md").write_text("# Other\n", encoding="utf-8")
        subprocess.run(["git", "add", "openspec"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "spec baseline"], cwd=root, check=True)
        ctx = context.bind(
            root, session_id="s", task_id="refund", task_type="important_change",
            spec_system="openspec", spec_ref="openspec/changes/refund",
        )
        evidence.record(
            root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="passed", source_ref="run-1",
        )

        (other / "proposal.md").write_text("# Other updated\n", encoding="utf-8")
        (other / "design.md").write_text("# Other design\n", encoding="utf-8")

        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

    def test_bound_spec_body_change_expires_task_evidence(self):
        root = git_repo()
        refund = root / "openspec" / "changes" / "refund"
        refund.mkdir(parents=True)
        proposal = refund / "proposal.md"
        proposal.write_text("# Refund\n", encoding="utf-8")
        ctx = context.bind(
            root, session_id="s", task_id="refund", task_type="important_change",
            spec_system="openspec", spec_ref="openspec/changes/refund",
        )
        evidence.record(
            root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="passed", source_ref="run-1",
        )
        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

        proposal.write_text("# Refund\n\nMust be idempotent.\n", encoding="utf-8")

        self.assertNotIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

    def test_code_change_marks_expiring_evidence_stale_without_deleting_history(self):
        root = git_repo()
        ctx = context.bind(
            root, session_id="s", task_id="small-fix",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        rec = evidence.record(
            root, ctx["context_id"], kind="tests", producer="pytest",
            result="pass", summary="1 passed", source_ref="pytest -q",
        )
        self.assertIn("tests", evidence.valid_kinds(root, ctx["context_id"]))

        (root / "src" / "app.py").write_text("print('v2')\n", encoding="utf-8")
        stale = evidence.refresh_staleness(root, ctx["context_id"])

        self.assertEqual(stale, [rec["evidence_id"]])
        self.assertNotIn("tests", evidence.valid_kinds(root, ctx["context_id"]))
        self.assertEqual(evidence.load(root, ctx["context_id"], rec["evidence_id"])["status"], "stale")

    def test_latest_failing_result_supersedes_older_pass_for_same_kind(self):
        root = git_repo()
        ctx = context.bind(
            root, session_id="s", task_id="fix",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        passed = evidence.record(
            root, ctx["context_id"], kind="tests", producer="unittest",
            result="pass", summary="passed", source_ref="run-1",
        )
        failed = evidence.record(
            root, ctx["context_id"], kind="tests", producer="unittest",
            result="fail", summary="failed", source_ref="run-2",
        )

        self.assertNotIn("tests", evidence.valid_kinds(root, ctx["context_id"]))
        self.assertEqual(evidence.load(root, ctx["context_id"], passed["evidence_id"])["status"], "superseded")
        self.assertEqual(evidence.load(root, ctx["context_id"], failed["evidence_id"])["status"], "active")

    def test_evidence_requires_existing_context(self):
        root = git_repo()
        with self.assertRaisesRegex(evidence.EvidenceError, "上下文不存在"):
            evidence.record(
                root, "missing", kind="tests", producer="unittest",
                result="pass", summary="passed", source_ref="run",
            )


class GovernanceTest(unittest.TestCase):
    def setUp(self):
        self.root = git_repo()
        self.spec = self.root / "openspec" / "changes" / "refund"
        self.spec.mkdir(parents=True)

    def test_remediation_paths_remain_open_without_context(self):
        self.assertTrue(governance.evaluate(self.root, "read", session_id="s")["allowed"])
        self.assertTrue(governance.evaluate(self.root, "spec_write", session_id="s")["allowed"])
        denied = governance.evaluate(self.root, "code_write", session_id="s")
        self.assertFalse(denied["allowed"])
        self.assertEqual(denied["envelope"]["code"], "governance_context_required")
        self.assertIn("spec_write", denied["envelope"]["allowed_actions"])

    def test_read_only_context_blocks_test_and_code_writes(self):
        context.bind(
            self.root, session_id="s", task_id="analysis",
            task_type="read_only", spec_system="none", spec_ref=None,
        )
        for action in ("test_write", "code_write"):
            denied = governance.evaluate(self.root, action, session_id="s")
            self.assertFalse(denied["allowed"], action)
            self.assertEqual(denied["envelope"]["code"], "governance_read_only_context")

    def test_important_change_requires_binding_and_explicit_scope_approval(self):
        ctx = context.bind(
            self.root, session_id="s", task_id="refund",
            task_type="important_change", spec_system="openspec",
            spec_ref="openspec/changes/refund",
        )
        self.assertTrue(governance.evaluate(self.root, "test_write", session_id="s")["allowed"])
        denied = governance.evaluate(self.root, "code_write", session_id="s")
        self.assertEqual(denied["envelope"]["code"], "governance_approval_required")

        context.approve(self.root, ctx["context_id"], "scope_approved", actor="user")
        denied = governance.evaluate(self.root, "code_write", session_id="s")
        self.assertEqual(denied["envelope"]["code"], "governance_stage_required")
        with patch.object(governance.stage_docs, "missing_before", return_value=[]):
            self.assertTrue(governance.evaluate(self.root, "code_write", session_id="s")["allowed"])

    def test_commit_requires_current_test_static_and_semantic_evidence(self):
        ctx = context.bind(
            self.root, session_id="s", task_id="small-fix",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        denied = governance.evaluate(self.root, "git_commit", session_id="s")
        self.assertEqual(denied["envelope"]["code"], "governance_stage_required")
        self.assertFalse(
            (self.root / ".flowguard" / "evidence").exists(),
            "只读门禁检查不能创建空证据目录",
        )
        with patch.object(governance.stage_docs, "missing_before", return_value=[]):
            denied = governance.evaluate(self.root, "git_commit", session_id="s")
            self.assertEqual(denied["envelope"]["missing"],
                             ["tests", "static_analysis", "semantic_review"])
        for kind in ("tests", "static_analysis", "semantic_review"):
            evidence.record(
                self.root, ctx["context_id"], kind=kind, producer="test",
                result="pass", summary=f"{kind} passed", source_ref=kind,
            )
        with patch.object(governance.stage_docs, "missing_before", return_value=[]):
            self.assertTrue(governance.evaluate(self.root, "git_commit", session_id="s")["allowed"])

    def test_advisory_codereview_does_not_suggest_manual_pass(self):
        ctx = context.bind(
            self.root, session_id="s", task_id="small-fix",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        for kind in ("tests", "static_analysis"):
            evidence.record(
                self.root, ctx["context_id"], kind=kind, producer="test",
                result="pass", summary=f"{kind} passed", source_ref=kind,
            )
        evidence.record(
            self.root, ctx["context_id"], kind="semantic_review",
            producer="hook:codereview-cli", result="warning",
            summary="CodeReview 已完成建议性审查；有限覆盖且无自动放行结论",
            source_ref="codereview-output-sha256:abcd1234",
        )

        with patch.object(governance.stage_docs, "missing_before", return_value=[]):
            denied = governance.evaluate(self.root, "git_commit", session_id="s")

        self.assertFalse(denied["allowed"])
        self.assertEqual(denied["envelope"]["code"], "governance_semantic_review_advisory")
        self.assertEqual(denied["envelope"]["missing"], ["semantic_review"])
        self.assertIn("可信放行依据", denied["envelope"]["message"])
        self.assertNotIn("evidence record", denied["envelope"]["fix"])

    def test_commit_denied_when_git_evidence_snapshot_cannot_be_read(self):
        ctx = context.bind(
            self.root, session_id="s", task_id="small-fix",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        for kind in governance.COMMIT_EVIDENCE:
            evidence.record(
                self.root, ctx["context_id"], kind=kind, producer="fixture",
                result="pass", summary="passed", source_ref=f"run:{kind}",
            )
        original_git = evidence._git

        for failing_command in ("diff", "ls-files"):
            with self.subTest(failing_command=failing_command):
                def fail_git(root, *args, **kwargs):
                    if args and args[0] == failing_command:
                        return subprocess.CompletedProcess(["git", *args], 1, b"", b"index unavailable")
                    return original_git(root, *args, **kwargs)

                with patch.object(evidence, "_git", side_effect=fail_git):
                    with patch.object(governance.stage_docs, "missing_before", return_value=[]):
                        result = governance.evaluate(self.root, "git_commit", session_id="s")

                self.assertFalse(result["allowed"])
                self.assertEqual(result["envelope"]["code"], "governance_git_state_unavailable")

    def test_release_requires_release_evidence_and_completed_children(self):
        parent = context.bind(
            self.root, session_id="s", task_id="release-train",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        child = context.bind(
            self.root, session_id="s", task_id="refund-child",
            task_type="simple_change", spec_system="none", spec_ref=None,
            parent_id=parent["context_id"],
        )
        context.bind(
            self.root, session_id="s", task_id="release-train",
            task_type="simple_change", spec_system="none", spec_ref=None,
        )
        denied = governance.evaluate(self.root, "release", session_id="s")
        self.assertEqual(denied["envelope"]["code"], "governance_stage_required")
        with patch.object(governance.stage_docs, "missing_before", return_value=[]):
            denied = governance.evaluate(self.root, "release", session_id="s")
            self.assertEqual(denied["envelope"]["code"], "governance_dependencies_incomplete")

        context.complete(self.root, child["context_id"])
        for kind in (*governance.COMMIT_EVIDENCE, *governance.RELEASE_EVIDENCE):
            evidence.record(
                self.root, parent["context_id"], kind=kind, producer="test",
                result="pass", summary=f"{kind} passed", source_ref=kind,
            )
        with patch.object(governance.stage_docs, "missing_before", return_value=[]):
            self.assertTrue(governance.evaluate(self.root, "release", session_id="s")["allowed"])


if __name__ == "__main__":
    unittest.main()
