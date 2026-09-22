import io, json, unittest
from contextlib import redirect_stderr, redirect_stdout
from scripts.flowgate_lib import diag

class EnvelopeTest(unittest.TestCase):
    def test_four_keys(self):
        env = diag.envelope("ERROR", "gate_write_code_tdd", "先验收测试用例", "运行 /flowgate-advance")
        self.assertEqual(set(env), {"severity", "code", "message", "fix"})
        self.assertEqual(env["severity"], "ERROR")

    def test_bad_severity_rejected(self):
        with self.assertRaises(AssertionError):
            diag.envelope("FATAL", "c", "m", "f")

class EmitTest(unittest.TestCase):
    def test_human_mode_two_lines_on_stderr(self):
        err, out = io.StringIO(), io.StringIO()
        with redirect_stderr(err), redirect_stdout(out):
            diag.emit(diag.envelope("WARNING", "w1", "消息", "修复"), as_json=False)
        self.assertIn("WARNING: 消息", err.getvalue())
        self.assertIn("Fix: 修复", err.getvalue())
        self.assertEqual(out.getvalue(), "")

    def test_json_mode_one_line_on_stdout(self):
        err, out = io.StringIO(), io.StringIO()
        with redirect_stderr(err), redirect_stdout(out):
            diag.emit(diag.envelope("INFO", "i1", "消息", "修复"), as_json=True)
        parsed = json.loads(out.getvalue().strip())
        self.assertEqual(parsed["code"], "i1")
        self.assertEqual(err.getvalue(), "")

if __name__ == "__main__":
    unittest.main()
