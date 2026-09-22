"""journal-restore 验收用例（TC-1~TC-5 ↔ journal-restore/REQ-1~3）。

TDD 先行：测试文件先于实现创建（执行证据最小版 = 文件存在）。
实现落地后移除 skip。
"""
import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "scripts" / "flowguard_state.py"

try:
    from scripts.flowguard_lib import recover
except ImportError:  # 实现未落地阶段
    recover = None


def run(root, *argv):
    return subprocess.run([sys.executable, str(CLI), *argv], cwd=root,
                          capture_output=True, text=True)


def seed_project(root):
    (root / "pom.xml").write_text("<project/>", encoding="utf-8")
    assert run(root, "init", "--json").returncode == 0
    assert run(root, "feature", "new", "f1", "--modules", "app", "--json").returncode == 0
    assert run(root, "next", "--json").returncode == 0


class RecoverTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        seed_project(self.root)

    @unittest.skipIf(recover is None, "REQ-1 实现后启用（TC-1 全量重建）")
    def test_tc1_full_rebuild(self):
        # TC-1 | REQ-1：全量丢失后重建，内容一致
        before = json.loads((self.root / ".flowguard" / "project.json").read_text())
        (self.root / ".flowguard" / "project.json").unlink()
        shutil.rmtree(self.root / ".flowguard" / "features")
        rep = recover.rebuild(self.root)
        self.assertTrue(rep["rebuilt"])
        after = json.loads((self.root / ".flowguard" / "project.json").read_text())
        self.assertEqual(after["features"], before["features"])

    @unittest.skipIf(recover is None, "REQ-1 实现后启用（TC-2 部分重建）")
    def test_tc2_partial_rebuild(self):
        # TC-2 | REQ-1：只重建缺失文件，完好的不改写
        (self.root / ".flowguard" / "features" / "f1" / "state.json").unlink()
        proj = self.root / ".flowguard" / "project.json"
        proj.write_text(proj.read_text() + "\n", encoding="utf-8")
        before_proj = proj.read_text()
        rep = recover.rebuild(self.root)
        self.assertEqual(proj.read_text(), before_proj)

    @unittest.skipIf(recover is None, "REQ-2 实现后启用（TC-3 冲突保护）")
    def test_tc3_conflict_protection(self):
        # TC-3 | REQ-2：冲突默认拒绝覆盖，--force 才覆盖
        proj = self.root / ".flowguard" / "project.json"
        proj.unlink()
        proj.write_text('{"tampered": true}', encoding="utf-8")
        rep = recover.rebuild(self.root)
        self.assertTrue(any(s.get("reason") == "conflict" for s in rep["skipped"]))
        self.assertEqual(json.loads(proj.read_text()), {"tampered": True})

    @unittest.skipIf(recover is None, "REQ-2 实现后启用（TC-4 恢复留痕）")
    def test_tc4_recovery_journaled(self):
        # TC-4 | REQ-2：重建后 journal 有 recover 事件
        (self.root / ".flowguard" / "project.json").unlink()
        recover.rebuild(self.root, force=True)
        jl = (self.root / ".flowguard" / "journal" / "events.jsonl").read_text()
        self.assertIn('"event": "recover"', jl)

    @unittest.skipIf(recover is None, "REQ-3 实现后启用（TC-5 dry-run）")
    def test_tc5_dry_run_no_writes(self):
        # TC-5 | REQ-3：dry-run 报告但零落盘
        (self.root / ".flowguard" / "project.json").unlink()
        rep = recover.rebuild(self.root, dry_run=True)
        self.assertTrue(rep["rebuilt"])
        self.assertFalse((self.root / ".flowguard" / "project.json").exists())


if __name__ == "__main__":
    unittest.main()
