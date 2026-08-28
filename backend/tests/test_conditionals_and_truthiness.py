"""
Unit tests for Python conditional expressions (ternaries) and truthiness
across Java, C++, and JavaScript code generators.
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.translation import TranslationEngine


class TestConditionalsAndTruthiness(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()

    def _translate(self, code: str):
        ir_prog = build_ir(code)
        java_out = self.engine.translate(ir_prog, "java")
        cpp_out = self.engine.translate(ir_prog, "cpp")
        js_out = self.engine.translate(ir_prog, "javascript")
        return java_out, cpp_out, js_out

    def test_conditional_expression_assignment(self):
        code = "x = 10 if flag else 20"
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("(flag ? 10 : 20)", java_out)
        self.assertIn("(flag ? 10 : 20)", cpp_out)
        self.assertIn("(flag ? 10 : 20)", js_out)

    def test_conditional_expression_in_return(self):
        code = """
def check(val: int) -> int:
    return 1 if val > 0 else -1
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("return (val > 0 ? 1 : -1);", java_out)
        self.assertIn("return (val > 0 ? 1 : -1);", cpp_out)
        self.assertIn("return (val > 0 ? 1 : -1);", js_out)

    def test_nested_ternary(self):
        code = "x = 1 if a else (2 if b else 3)"
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("? 1 : (b ? 2 : 3)", java_out)
        self.assertIn("? 1 : (b ? 2 : 3)", cpp_out)
        self.assertIn("? 1 : (b ? 2 : 3)", js_out)


if __name__ == "__main__":
    unittest.main()
