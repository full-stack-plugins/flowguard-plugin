import unittest
from scripts.flowguard_lib import registry


class StructureTest(unittest.TestCase):
    def test_ten_artifacts(self):
        self.assertEqual(len(registry.ARTIFACTS), 10)
        self.assertEqual(registry.STAGE_ORDER[2], "solution")
        self.assertEqual(registry.STAGE_ORDER[4:6], ("hld", "lld"))

    def test_acyclic_real_registry(self):
        registry.check_acyclic()  # 不抛即通过

    def test_acyclic_detects_cycle(self):
        bad = {"a": {"requires": ("b",)}, "b": {"requires": ("a",)}}
        with self.assertRaises(registry.StateError):
            registry._check_acyclic_graph(bad)

    def test_topo_requirements_before_testcases(self):
        order = registry.topo_order()
        self.assertLess(order.index("01-requirements"), order.index("04-testcases"))
        self.assertLess(order.index("05-hld"), order.index("06-lld"))


if __name__ == "__main__":
    unittest.main()
