"""
Rosetta AI - Lambdas and Advanced Parameters Unit Tests (Phase 13)
------------------------------------------------------------------
Tests lambda expressions, *args, **kwargs, and positional/keyword parameter metadata across targets.
"""

import unittest
from app.translation.engine import TranslationEngine
from app.translation.java_generator import JavaGenerator
from app.translation.cpp_generator import CppGenerator
from app.translation.javascript_generator import JavaScriptGenerator
from app.ir.builder import build_ir


class TestLambdasAndParams(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()
        self.engine.register_generator("java", JavaGenerator())
        self.engine.register_generator("cpp", CppGenerator())
        self.engine.register_generator("javascript", JavaScriptGenerator())

    def test_single_arg_lambda(self):
        code = """
def apply_fn():
    sq = lambda x: x * x
    return sq(5)
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("x -> x * x", java)
        self.assertIn("[&](auto x)", cpp)
        self.assertIn("x => x * x", js)

    def test_multi_arg_lambda(self):
        code = """
def apply_add():
    add_fn = lambda a, b: a + b
    return add_fn(2, 3)
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("(a, b) -> a + b", java)
        self.assertIn("[&](auto a, auto b)", cpp)
        self.assertIn("(a, b) => a + b", js)

    def test_ir_parameter_classification(self):
        code = """
def complex_fn(a, /, b, c=10, *args, d=20, **kwargs):
    return a + b + c + d
"""
        ir = build_ir(code)
        fn = ir.functions[0]
        self.assertEqual(fn.posonly_parameters, ["a"])
        self.assertEqual(fn.vararg, "args")
        self.assertEqual(fn.kwarg, "kwargs")
        self.assertIn("d", fn.kwonly_parameters)


if __name__ == "__main__":
    unittest.main()
