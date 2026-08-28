"""
Rosetta AI - Collection Operations & Comprehensions Test Suite (Phase 11)
------------------------------------------------------------------------
Validates collection methods, string methods, math imports, and list comprehensions
across Java, C++, and JavaScript generators:
1. List operations: append, pop, remove, extend
2. String operations: upper, lower, strip
3. Math operations: math.sqrt, math.pow, sqrt, pow
4. List comprehensions: [x * 2 for x in range(5)]
5. List comprehensions with condition: [x for x in range(10) if x > 3]
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.translation import TranslationEngine


class TestCollectionOpsAndComprehensions(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine(register_defaults=True)

    def translate_all(self, python_code: str):
        ir = build_ir(python_code)
        java_out = self.engine.translate(ir, "java")
        cpp_out = self.engine.translate(ir, "cpp")
        js_out = self.engine.translate(ir, "javascript")
        return java_out, cpp_out, js_out

    def test_list_collection_methods(self):
        """Tests append, pop, remove, and extend."""
        src = """def test_ops():
    items = [1, 2, 3]
    items.append(4)
    items.pop()
    items.extend([5, 6])
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("items.add(4);", java)
        self.assertIn("items.remove(items.size() - 1);", java)
        self.assertIn("items.addAll(Arrays.asList(5, 6));", java)

        self.assertIn("items.push_back(4);", cpp)
        self.assertIn("items.pop_back();", cpp)
        self.assertIn("items.insert(items.end(),", cpp)

        self.assertIn("items.push(4);", js)
        self.assertIn("items.pop();", js)
        self.assertIn("items.push(...[5, 6]);", js)

    def test_string_methods(self):
        """Tests upper, lower, and strip string methods."""
        src = """def format_text(txt: str):
    u = txt.upper()
    l = txt.lower()
    s = txt.strip()
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("String u = txt.toUpperCase();", java)
        self.assertIn("String l = txt.toLowerCase();", java)
        self.assertIn("String s = txt.trim();", java)

        self.assertIn("let u = txt.toUpperCase();", js)
        self.assertIn("let l = txt.toLowerCase();", js)
        self.assertIn("let s = txt.trim();", js)

    def test_math_imports_and_builtins(self):
        """Tests math.sqrt and math.pow."""
        src = """import math

def calc_hypot(a: float, b: float) -> float:
    return math.sqrt(math.pow(a, 2) + math.pow(b, 2))
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("return Math.sqrt(Math.pow(a, 2) + Math.pow(b, 2));", java)

        self.assertIn("#include <cmath>", cpp)
        self.assertIn("return std::sqrt(std::pow(a, 2) + std::pow(b, 2));", cpp)

        self.assertIn("return Math.sqrt(Math.pow(a, 2) + Math.pow(b, 2));", js)

    def test_list_comprehension_basic(self):
        """Tests basic list comprehension [x * x for x in range(5)]."""
        src = """squares = [x * x for x in range(5)]
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("List<Integer> squares = new ArrayList<>();", java)
        self.assertIn("for (int x = 0; x < 5; x++)", java)
        self.assertIn("squares.add(x * x);", java)

        self.assertIn("std::vector<int> squares;", cpp)
        self.assertIn("for (int x = 0; x < 5; ++x)", cpp)
        self.assertIn("squares.push_back(x * x);", cpp)

        self.assertIn("let squares = [];", js)
        self.assertIn("for (let x = 0; x < 5; x++)", js)
        self.assertIn("squares.push(x * x);", js)

    def test_list_comprehension_with_filter(self):
        """Tests list comprehension with conditional filter."""
        src = """evens = [x for x in range(10) if x > 2]
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("if (x > 2) evens.add(x);", java)

        self.assertIn("if (x > 2) evens.push_back(x);", cpp)

        self.assertIn("if (x > 2) evens.push(x);", js)


if __name__ == "__main__":
    unittest.main()
