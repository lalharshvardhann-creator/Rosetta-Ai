"""
Rosetta AI - Builtin Iterators and Aggregations Unit Tests (Phase 13)
---------------------------------------------------------------------
Tests enumerate, zip, sum, any, all, sorted, and reversed across Java, C++, and JavaScript.
"""

import unittest
from app.translation.engine import TranslationEngine
from app.translation.java_generator import JavaGenerator
from app.translation.cpp_generator import CppGenerator
from app.translation.javascript_generator import JavaScriptGenerator


class TestBuiltinIterators(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()
        self.engine.register_generator("java", JavaGenerator())
        self.engine.register_generator("cpp", CppGenerator())
        self.engine.register_generator("javascript", JavaScriptGenerator())

    def test_enumerate_loop(self):
        code = """
def print_indexed(items):
    for i, x in enumerate(items):
        print(i, x)
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("items.size()", java)
        self.assertIn("items.get(i)", java)

        self.assertIn("items.size()", cpp)
        self.assertIn("items[i]", cpp)

        self.assertIn("items.length", js)
        self.assertIn("items[i]", js)

    def test_zip_loop(self):
        code = """
def pair_items(xs, ys):
    for a, b in zip(xs, ys):
        print(a, b)
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("Math.min(xs.size(), ys.size())", java)
        self.assertIn("std::min(xs.size(), ys.size())", cpp)
        self.assertIn("Math.min(xs.length, ys.length)", js)

    def test_sum_builtin(self):
        code = """
def calculate_sum(numbers):
    return sum(numbers)
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn(".stream().mapToInt(Integer::intValue).sum()", java)
        self.assertIn("std::accumulate(numbers.begin(), numbers.end(), 0)", cpp)
        self.assertIn("numbers.reduce((a, b) => a + b, 0)", js)

    def test_any_and_all_builtins(self):
        code = """
def verify_flags(flags):
    has_any = any(flags)
    has_all = all(flags)
    return has_any
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("anyMatch", java)
        self.assertIn("allMatch", java)

        self.assertIn("std::any_of", cpp)
        self.assertIn("std::all_of", cpp)

        self.assertIn("some", js)
        self.assertIn("every", js)

    def test_sorted_and_reversed_builtins(self):
        code = """
def transform_list(items):
    s = sorted(items)
    r = reversed(items)
    return s
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("ArrayList", java)
        self.assertIn("std::sort", cpp)
        self.assertIn("std::reverse", cpp)
        self.assertIn("sort", js)
        self.assertIn("reverse", js)


if __name__ == "__main__":
    unittest.main()
