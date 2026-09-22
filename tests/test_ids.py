import unittest
from scripts.flowguard_lib import ids

class KebabTest(unittest.TestCase):
    def test_samples(self):
        self.assertTrue(ids.is_kebab("order-refund"))
        self.assertTrue(ids.is_kebab("req1"))
        self.assertFalse(ids.is_kebab("Order"))
        self.assertFalse(ids.is_kebab("a--b"))
        self.assertFalse(ids.is_kebab("-x"))
        self.assertFalse(ids.is_kebab("x-"))
        self.assertFalse(ids.is_kebab(""))

class ReqIdTest(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(ids.req_id("order-refund", 3), "order-refund/REQ-3")
        self.assertEqual(ids.parse_req_id("order-refund/REQ-3"), ("order-refund", 3))

    def test_parse_invalid(self):
        self.assertIsNone(ids.parse_req_id("bad"))
        self.assertIsNone(ids.parse_req_id("f/REQ-x"))
        self.assertIsNone(ids.parse_req_id(None))

    def test_fold_name(self):
        self.assertEqual(ids.fold_name("### 订单退款申请 ##"), "订单退款申请")
        self.assertEqual(ids.fold_name("  Foo   Bar  "), "foo bar")

if __name__ == "__main__":
    unittest.main()
