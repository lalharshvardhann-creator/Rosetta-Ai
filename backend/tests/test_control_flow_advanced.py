"""
Rosetta AI - Advanced Control Flow Unit Tests (Phase 13)
--------------------------------------------------------
Tests break, continue, for/else, and while/else semantics across Java, C++, and JavaScript.
"""

import unittest
from app.translation.engine import TranslationEngine
from app.translation.java_generator import JavaGenerator
from app.translation.cpp_generator import CppGenerator
from app.translation.javascript_generator import JavaScriptGenerator


class TestAdvancedControlFlow(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()
        self.engine.register_generator("java", JavaGenerator())
        self.engine.register_generator("cpp", CppGenerator())
        self.engine.register_generator("javascript", JavaScriptGenerator())

    def test_break_and_continue_in_for_loop(self):
        code = """
def process(items):
    total = 0
    for x in items:
        if x < 0:
            continue
        if x > 100:
            break
        total = total + x
    return total
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("continue;", java)
        self.assertIn("break;", java)
        self.assertIn("continue;", cpp)
        self.assertIn("break;", cpp)
        self.assertIn("continue;", js)
        self.assertIn("break;", js)

    def test_break_and_continue_in_while_loop(self):
        code = """
def countdown(n):
    while n > 0:
        n = n - 1
        if n == 2:
            continue
        if n == 0:
            break
    return n
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("continue;", java)
        self.assertIn("break;", java)
        self.assertIn("continue;", cpp)
        self.assertIn("break;", cpp)
        self.assertIn("continue;", js)
        self.assertIn("break;", js)

    def test_for_else_construct(self):
        code = """
def find_item(items, target):
    found = 0
    for x in items:
        if x == target:
            found = 1
            break
    else:
        found = -1
    return found
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("_completed", java)
        self.assertIn("if (_completed)", java)
        self.assertIn("_completed", cpp)
        self.assertIn("if (_completed)", cpp)
        self.assertIn("_completed", js)
        self.assertIn("if (_completed)", js)

    def test_while_else_construct(self):
        code = """
def search_while(n):
    status = 0
    while n > 0:
        if n == 5:
            break
        n = n - 1
    else:
        status = 1
    return status
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("_completed", java)
        self.assertIn("if (_completed)", java)
        self.assertIn("_completed", cpp)
        self.assertIn("if (_completed)", cpp)
        self.assertIn("_completed", js)
        self.assertIn("if (_completed)", js)


if __name__ == "__main__":
    unittest.main()
