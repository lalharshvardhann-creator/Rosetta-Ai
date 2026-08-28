"""
Rosetta AI - Classes and OOP Test Suite (Phase 11)
--------------------------------------------------
Validates Python OOP / class translation to Java, C++, and JavaScript:
1. Class definitions with __init__ constructors
2. Instance attribute assignments (self.attr = value)
3. Instance method generation (omitting self in headers)
4. Field declarations and type inference
5. Class instantiation and method invocation
6. Multiple instance methods and multiple classes
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.translation import TranslationEngine


class TestClassesAndOOP(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine(register_defaults=True)

    def translate_all(self, python_code: str):
        ir = build_ir(python_code)
        java_out = self.engine.translate(ir, "java")
        cpp_out = self.engine.translate(ir, "cpp")
        js_out = self.engine.translate(ir, "javascript")
        return java_out, cpp_out, js_out

    def test_basic_class_with_constructor(self):
        """Tests a basic class with constructor and instance variable."""
        src = """class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("public class Point", java)
        self.assertIn("public int x;", java)
        self.assertIn("public int y;", java)
        self.assertIn("public Point(int x, int y)", java)
        self.assertIn("this.x = x;", java)
        self.assertIn("this.y = y;", java)

        self.assertIn("class Point", cpp)
        self.assertIn("int x;", cpp)
        self.assertIn("int y;", cpp)
        self.assertIn("Point(int x, int y)", cpp)
        self.assertIn("this->x = x;", cpp)
        self.assertIn("this->y = y;", cpp)

        self.assertIn("class Point", js)
        self.assertIn("constructor(x, y)", js)
        self.assertIn("this.x = x;", js)
        self.assertIn("this.y = y;", js)

    def test_class_with_instance_methods(self):
        """Tests a class with multiple instance methods manipulating state."""
        src = """class Counter:
    def __init__(self, initial: int):
        self.count = initial

    def increment(self, step: int):
        self.count = self.count + step

    def get_count(self) -> int:
        return self.count
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("public void increment(int step)", java)
        self.assertIn("public int get_count()", java)
        self.assertIn("return this.count;", java)

        self.assertIn("void increment(int step)", cpp)
        self.assertIn("int get_count()", cpp)
        self.assertIn("return this->count;", cpp)

        self.assertIn("increment(step)", js)
        self.assertIn("get_count()", js)
        self.assertIn("return this.count;", js)

    def test_class_instantiation_and_calls(self):
        """Tests instantiating a class and calling its methods."""
        src = """class Calculator:
    def __init__(self, base: int):
        self.base = base

    def add(self, n: int) -> int:
        return self.base + n

c = Calculator(10)
result = c.add(5)
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("Calculator c = new Calculator(10);", java)
        self.assertIn("c.add(5);", java)

        self.assertIn("Calculator c = Calculator(10);", cpp)
        self.assertIn("auto result = c.add(5);", cpp)

        self.assertIn("let c = new Calculator(10);", js)
        self.assertIn("let result = c.add(5);", js)


if __name__ == "__main__":
    unittest.main()
