"""
Rosetta AI - Sets and Advanced Comprehensions Unit Tests (Phase 13)
-------------------------------------------------------------------
Tests set literals, set operations, set comprehensions, and dictionary comprehensions across Java, C++, and JavaScript.
"""

import unittest
from app.translation.engine import TranslationEngine
from app.translation.java_generator import JavaGenerator
from app.translation.cpp_generator import CppGenerator
from app.translation.javascript_generator import JavaScriptGenerator


class TestSetsAndComprehensions(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()
        self.engine.register_generator("java", JavaGenerator())
        self.engine.register_generator("cpp", CppGenerator())
        self.engine.register_generator("javascript", JavaScriptGenerator())

    def test_set_literal_translation(self):
        code = """
def make_set():
    s = {1, 2, 3}
    return s
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("HashSet", java)
        self.assertIn("std::set", cpp)
        self.assertIn("new Set([1, 2, 3])", js)

    def test_set_operations_translation(self):
        code = """
def set_ops(s):
    s.add(4)
    s.remove(1)
    s.discard(2)
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("s.add(4)", java)
        self.assertIn("s.remove(1)", java)
        self.assertIn("s.remove(2)", java)

        self.assertIn("s.insert(4)", cpp)
        self.assertIn("s.erase(1)", cpp)
        self.assertIn("s.erase(2)", cpp)

        self.assertIn("s.add(4)", js)
        self.assertIn("s.delete(1)", js)
        self.assertIn("s.delete(2)", js)

    def test_set_comprehension(self):
        code = """
def double_set():
    doubles = {x * 2 for x in range(5)}
    return doubles
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("Set<Integer> doubles = new HashSet<>();", java)
        self.assertIn("doubles.add(x * 2);", java)

        self.assertIn("std::set<int> doubles;", cpp)
        self.assertIn("doubles.insert(x * 2);", cpp)

        self.assertIn("let doubles = new Set();", js)
        self.assertIn("doubles.add(x * 2);", js)

    def test_dict_comprehension(self):
        code = """
def square_dict():
    squares = {x: x * x for x in range(4)}
    return squares
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("Map<Integer, Integer> squares = new HashMap<>();", java)
        self.assertIn("squares.put(x, x * x);", java)

        self.assertIn("std::map<int, int> squares;", cpp)
        self.assertIn("squares[x] = x * x;", cpp)

        self.assertIn("let squares = {};", js)
        self.assertIn("squares[x] = x * x;", js)


if __name__ == "__main__":
    unittest.main()
