"""state 工具语义直接单测：锁互斥、原子写失败保留旧文、原子创建不覆盖。"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from flowguard_lib import state


class StateLockTest(unittest.TestCase):
    def test_lock_conflict_raises_state_error(self):
        root = Path(tempfile.mkdtemp())
        with state.state_lock(root):
            with self.assertRaisesRegex(state.StateError, "锁定"):
                with state.state_lock(root):
                    pass

    def test_lock_released_after_exit(self):
        root = Path(tempfile.mkdtemp())
        with state.state_lock(root):
            pass
        with state.state_lock(root):  # 不抛即可
            pass


class AtomicWriteTest(unittest.TestCase):
    def test_atomic_write_replaces_content(self):
        target = Path(tempfile.mkdtemp()) / "doc.md"
        state.atomic_write_text(target, "旧")
        state.atomic_write_text(target, "新")
        self.assertEqual(target.read_text(encoding="utf-8"), "新")

    def test_atomic_write_failure_preserves_old_content(self):
        target = Path(tempfile.mkdtemp()) / "doc.md"
        state.atomic_write_text(target, "旧正文")
        with mock.patch("os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                state.atomic_write_text(target, "新正文")
        self.assertEqual(target.read_text(encoding="utf-8"), "旧正文")
        self.assertEqual(list(target.parent.glob("*")), [target])

    def test_atomic_create_does_not_overwrite(self):
        target = Path(tempfile.mkdtemp()) / "doc.md"
        state.atomic_create_text(target, "初版")
        with self.assertRaises(FileExistsError):
            state.atomic_create_text(target, "覆盖企图")
        self.assertEqual(target.read_text(encoding="utf-8"), "初版")

    def test_atomic_create_failure_leaves_no_partial_or_residue(self):
        target = Path(tempfile.mkdtemp()) / "doc.md"
        with mock.patch("os.link", side_effect=OSError("link failed")):
            with self.assertRaises(OSError):
                state.atomic_create_text(target, "半成品")
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.glob(".fg-atomic-*")), [])


@unittest.skipUnless(sys.platform == "win32", "msvcrt 锁仅 Windows 路径")
class WindowsLockSmokeTest(unittest.TestCase):
    def test_basic_lock_round_trip(self):
        root = Path(tempfile.mkdtemp())
        with state.state_lock(root):
            pass


if __name__ == "__main__":
    unittest.main()
