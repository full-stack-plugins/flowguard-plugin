import datetime, tempfile, unittest
from pathlib import Path
from scripts.flowgate_lib import journal

class JournalTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_append_and_read_order(self):
        journal.append(self.root, "feature:order-refund", "gate_block", {"code": "x"})
        journal.append(self.root, "project", "accepted", {"stage": "requirements"})
        recs = journal.read(self.root)
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0]["scope"], "feature:order-refund")
        self.assertEqual(recs[0]["event"], "gate_block")
        self.assertEqual(recs[1]["detail"]["stage"], "requirements")

    def test_timestamp_iso(self):
        journal.append(self.root, "project", "init", {})
        ts = journal.read(self.root)[0]["ts"]
        datetime.datetime.fromisoformat(ts)  # 不抛即可

    def test_read_empty(self):
        self.assertEqual(journal.read(self.root), [])

if __name__ == "__main__":
    unittest.main()
