"""
Unit tests for Python advanced function capabilities (default arguments, keywords, recursion)
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


class TestAdvancedFunctions(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()

    def _translate(self, code: str):
        ir_prog = build_ir(code)
        java_out = self.engine.translate(ir_prog, "java")
        cpp_out = self.engine.translate(ir_prog, "cpp")
        js_out = self.engine.translate(ir_prog, "javascript")
        return java_out, cpp_out, js_out

    def test_default_parameter_values(self):
        code = """
def greet(name: str, times: int = 1) -> None:
    pass
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("greet(", java_out)
        self.assertIn("int times = 1", cpp_out)
        self.assertIn("times = 1", js_out)

    def test_recursive_function(self):
        code = """
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("factorial(n - 1)", java_out)
        self.assertIn("factorial(n - 1)", cpp_out)
        self.assertIn("factorial(n - 1)", js_out)

    def test_math_constants_and_calls(self):
        code = """
import math
radius = 5.0
area = math.pi * math.pow(radius, 2)
root = math.sqrt(16.0)
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("Math.PI", java_out)
        self.assertIn("Math.pow(radius, 2)", java_out)
        self.assertIn("Math.sqrt(16.0)", java_out)

        self.assertIn("M_PI", cpp_out)
        self.assertIn("std::pow(radius, 2)", cpp_out)
        self.assertIn("std::sqrt(16.0)", cpp_out)

        self.assertIn("Math.PI", js_out)
        self.assertIn("Math.pow(radius, 2)", js_out)
        self.assertIn("Math.sqrt(16.0)", js_out)


if __name__ == "__main__":
    unittest.main()
