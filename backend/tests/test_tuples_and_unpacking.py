"""
Unit tests for Python tuple construction, multiple assignment, and unpacking
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


class TestTuplesAndUnpacking(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()

    def _translate(self, code: str):
        ir_prog = build_ir(code)
        java_out = self.engine.translate(ir_prog, "java")
        cpp_out = self.engine.translate(ir_prog, "cpp")
        js_out = self.engine.translate(ir_prog, "javascript")
        return java_out, cpp_out, js_out

    def test_tuple_literal_creation(self):
        code = "point = (10, 20)"
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("Arrays.asList(10, 20)", java_out)
        self.assertIn("std::make_tuple(10, 20)", cpp_out)
        self.assertIn("#include <tuple>", cpp_out)
        self.assertIn("[10, 20]", js_out)

    def test_multiple_assignment_constants(self):
        code = "a, b = 1, 2"
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("a = 1", java_out)
        self.assertIn("b = 2", java_out)
        self.assertIn("a = 1", cpp_out)
        self.assertIn("b = 2", cpp_out)
        self.assertIn("[a, b] = [1, 2]", js_out)

    def test_tuple_unpacking_from_variable(self):
        code = "point = (10, 20)\nx, y = point"
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("point.get(0)", java_out)
        self.assertIn("point.get(1)", java_out)
        self.assertIn("std::get<0>(point)", cpp_out)
        self.assertIn("std::get<1>(point)", cpp_out)
        self.assertIn("[x, y] = point", js_out)

    def test_function_returning_tuple(self):
        code = """
def get_coords():
    return (100, 200)
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("return Arrays.asList(100, 200);", java_out)
        self.assertIn("return std::make_tuple(100, 200);", cpp_out)
        self.assertIn("return [100, 200];", js_out)


if __name__ == "__main__":
    unittest.main()
