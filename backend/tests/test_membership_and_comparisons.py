"""
Rosetta AI - Membership and Chained Comparisons Unit Tests (Phase 13)
---------------------------------------------------------------------
Tests in/not in membership operators and chained comparison expressions across Java, C++, and JavaScript.
"""

import unittest
from app.translation.engine import TranslationEngine
from app.translation.java_generator import JavaGenerator
from app.translation.cpp_generator import CppGenerator
from app.translation.javascript_generator import JavaScriptGenerator


class TestMembershipAndComparisons(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()
        self.engine.register_generator("java", JavaGenerator())
        self.engine.register_generator("cpp", CppGenerator())
        self.engine.register_generator("javascript", JavaScriptGenerator())

    def test_in_operator_list(self):
        code = """
def check_item(items, val):
    if val in items:
        return 1
    return 0
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("items.contains(val)", java)
        self.assertIn("std::find(items.begin(), items.end(), val) != items.end()", cpp)
        self.assertIn("includes", js)

    def test_not_in_operator(self):
        code = """
def check_absent(items, val):
    if val not in items:
        return 1
    return 0
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("!items.contains(val)", java)
        self.assertIn("std::find(items.begin(), items.end(), val) == items.end()", cpp)
        self.assertIn("includes", js)

    def test_chained_comparison_range(self):
        code = """
def is_single_digit(x):
    if 0 <= x < 10:
        return 1
    return 0
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("0 <= x", java)
        self.assertIn("x < 10", java)
        self.assertIn("&&", java)

        self.assertIn("0 <= x", cpp)
        self.assertIn("x < 10", cpp)
        self.assertIn("&&", cpp)

        self.assertIn("0 <= x", js)
        self.assertIn("x < 10", js)
        self.assertIn("&&", js)

    def test_chained_comparison_three_ops(self):
        code = """
def in_bounds(a, b, c, d):
    return a < b < c < d
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("a < b", java)
        self.assertIn("b < c", java)
        self.assertIn("c < d", java)
        self.assertIn("&&", java)

        self.assertIn("a < b", cpp)
        self.assertIn("b < c", cpp)
        self.assertIn("c < d", cpp)
        self.assertIn("&&", cpp)

        self.assertIn("a < b", js)
        self.assertIn("b < c", js)
        self.assertIn("c < d", js)
        self.assertIn("&&", js)


if __name__ == "__main__":
    unittest.main()
