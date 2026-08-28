"""
Rosetta AI - Exception Handling Test Suite (Phase 11)
-----------------------------------------------------
Validates Python exception handling constructs translated across Java, C++, and JavaScript:
1. try / except block
2. try / except with alias (except Exception as e)
3. try / except / finally block
4. raise statements
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.translation import TranslationEngine


class TestExceptions(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine(register_defaults=True)

    def translate_all(self, python_code: str):
        ir = build_ir(python_code)
        java_out = self.engine.translate(ir, "java")
        cpp_out = self.engine.translate(ir, "cpp")
        js_out = self.engine.translate(ir, "javascript")
        return java_out, cpp_out, js_out

    def test_try_except_basic(self):
        """Tests basic try / except block translation."""
        src = """def safe_div(a: int, b: int) -> int:
    try:
        res = a / b
        return res
    except:
        return 0
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("try {", java)
        self.assertIn("catch (Exception e) {", java)
        self.assertIn("return 0;", java)

        self.assertIn("try {", cpp)
        self.assertIn("catch (const std::exception& e) {", cpp)
        self.assertIn("return 0;", cpp)

        self.assertIn("try {", js)
        self.assertIn("catch (e) {", js)
        self.assertIn("return 0;", js)

    def test_try_except_finally(self):
        """Tests try / except / finally translation."""
        src = """def process():
    try:
        x = 10
    except Exception as err:
        print("error")
    finally:
        print("cleanup")
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("try {", java)
        self.assertIn("catch (Exception err) {", java)
        self.assertIn("finally {", java)
        self.assertIn('System.out.println("cleanup");', java)

        self.assertIn("try {", cpp)
        self.assertIn("catch (const std::exception& err) {", cpp)
        self.assertIn('std::cout << "cleanup" << std::endl;', cpp)

        self.assertIn("try {", js)
        self.assertIn("catch (err) {", js)
        self.assertIn("finally {", js)
        self.assertIn('console.log("cleanup");', js)

    def test_raise_statement(self):
        """Tests raise statement translation."""
        src = """def check_positive(val: int):
    if val < 0:
        raise Exception("Value must be positive")
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn('throw new Exception("Value must be positive");', java)

        self.assertIn('#include <stdexcept>', cpp)
        self.assertIn('throw std::runtime_error(Exception("Value must be positive"));', cpp)

        self.assertIn('throw new Exception("Value must be positive");', js)


if __name__ == "__main__":
    unittest.main()
