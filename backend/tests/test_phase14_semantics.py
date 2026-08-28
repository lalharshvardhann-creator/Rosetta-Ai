"""
Rosetta AI - Phase 14 Unit Tests
---------------------------------
Comprehensive unit testing for Phase 14 features:
1. Python truthiness & None comparison semantics (is, is not)
2. Assert statements (with and without message)
3. Generator expressions in aggregation functions (sum, any, all)
4. Yield & generator functions (function* in JS, collection/stream in Java & C++)
5. Exception handling: multiple handlers, try/except/else/finally, bare raise
6. Range semantics with negative and variable step
7. Dictionary advanced operations (setdefault, keys, values, items)
8. Functional builtins (map, filter)
9. Reflection & type builtins (callable, type, isinstance, hasattr, getattr)
10. String operations (lstrip, rstrip, count, startswith, endswith, find)
11. Starred argument lowering (*args, **kwargs)
12. Cross-target end-to-end integration and consistency
"""

import unittest
from app.ir.builder import IRBuilder, build_ir
from app.ir.nodes import (
    IRAssert,
    IRBinaryOperation,
    IRGeneratorExpression,
    IRIsInstance,
    IRStarred,
    IRTry,
    IRYield,
)
from app.translation.engine import TranslationEngine


class TestPhase14Semantics(unittest.TestCase):
    def setUp(self):
        self.engine = TranslationEngine()
        self.builder = IRBuilder()

    def test_is_and_is_not_none_comparison(self):
        code = """
def check_val(x):
    if x is None:
        return True
    if x is not None:
        return False
    return x is 10
"""
        ir = build_ir(code)
        self.assertIsInstance(ir.functions[0].body[0].condition, IRBinaryOperation)
        self.assertEqual(ir.functions[0].body[0].condition.operator, "is")

        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("x == null", java)
        self.assertIn("x != null", java)

        self.assertIn("x == nullptr", cpp)
        self.assertIn("x != nullptr", cpp)

        self.assertIn("x === null", js)
        self.assertIn("x !== null", js)

    def test_assert_statement(self):
        code = """
def validate(n):
    assert n > 0
    assert n < 100, "Out of range"
"""
        ir = build_ir(code)
        self.assertIsInstance(ir.functions[0].body[0], IRAssert)
        self.assertIsInstance(ir.functions[0].body[1], IRAssert)
        self.assertIsNotNone(ir.functions[0].body[1].message)

        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("throw new AssertionError(", java)
        self.assertIn('"Out of range"', java)

        self.assertIn("throw std::runtime_error(", cpp)
        self.assertIn('"Out of range"', cpp)

        self.assertIn("throw new Error(", js)
        self.assertIn('"Out of range"', js)

    def test_generator_expressions_in_aggregations(self):
        code = """
def calc_metrics(items):
    total = sum(x * 2 for x in items if x > 0)
    has_pos = any(x > 5 for x in items)
    all_pos = all(x > 0 for x in items)
    return total
"""
        ir = build_ir(code)
        func = ir.functions[0]
        sum_call = func.body[0].value
        self.assertIsInstance(sum_call.arguments[0], IRGeneratorExpression)

        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertTrue("stream()" in java or "filter" in java)
        self.assertIn("for (const auto&", cpp)
        self.assertTrue("reduce" in js or "some" in js or "every" in js)

    def test_yield_and_generator_function(self):
        code = """
def count_up():
    yield 1
    yield 2
    yield 3
"""
        ir = build_ir(code)
        self.assertIsInstance(ir.functions[0].body[0].expression, IRYield)

        js = self.engine.translate(code, "javascript")
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")

        self.assertIn("function* count_up()", js)
        self.assertIn("yield 1;", js)

        self.assertIn("/* yield */", java)
        self.assertIn("/* yield */", cpp)

    def test_try_except_else_finally_and_multiple_handlers(self):
        code = """
def safe_calc(a, b):
    try:
        res = a / b
    except ValueError as ve:
        return -1
    except Exception as e:
        return 0
    else:
        print("Success")
    finally:
        print("Done")
"""
        ir = build_ir(code)
        try_node = ir.functions[0].body[0]
        self.assertIsInstance(try_node, IRTry)
        self.assertEqual(len(try_node.handlers), 2)
        self.assertTrue(len(try_node.else_body) > 0)
        self.assertTrue(len(try_node.finally_body) > 0)

        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("boolean _try_ok = true;", java)
        self.assertIn("catch (IllegalArgumentException ve)", java)
        self.assertIn("catch (Exception e)", java)
        self.assertIn("if (_try_ok)", java)
        self.assertIn("finally {", java)

        self.assertIn("bool _try_ok = true;", cpp)
        self.assertIn("catch (const std::invalid_argument& ve)", cpp)
        self.assertIn("catch (const std::exception& e)", cpp)
        self.assertIn("if (_try_ok)", cpp)

        self.assertIn("let _try_ok = true;", js)
        self.assertIn("if (_try_ok)", js)
        self.assertIn("finally {", js)

    def test_bare_raise_statement(self):
        code = """
def bubble():
    raise
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("throw new RuntimeException();", java)
        self.assertIn("throw;", cpp)
        self.assertIn("throw new Error();", js)

    def test_negative_range_step(self):
        code = """
def countdown():
    for i in range(10, 0, -1):
        print(i)
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("i > 0", java)
        self.assertIn("i += -1", java)

        self.assertIn("i > 0", cpp)
        self.assertIn("i += -1", cpp)

        self.assertIn("i > 0", js)
        self.assertIn("i += -1", js)

    def test_dict_advanced_operations(self):
        code = """
def dict_ops(data):
    data.setdefault("key", 100)
    k = data.keys()
    v = data.values()
    items = data.items()
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("data.putIfAbsent(", java)
        self.assertIn("data.keySet()", java)
        self.assertIn("data.values()", java)
        self.assertIn("data.entrySet()", java)

        self.assertIn("data.find(", cpp)

        self.assertIn("Object.keys(data)", js)
        self.assertIn("Object.values(data)", js)
        self.assertIn("Object.entries(data)", js)

    def test_map_and_filter_builtins(self):
        code = """
def transform(items):
    doubled = map(lambda x: x * 2, items)
    evens = filter(lambda x: x % 2 == 0, items)
    return items
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("stream().map(", java)
        self.assertIn("stream().filter(", java)

        self.assertIn(".map(", js)
        self.assertIn(".filter(", js)

    def test_type_and_reflection_builtins(self):
        code = """
def inspect_val(x):
    is_num = isinstance(x, int)
    is_fn = callable(x)
    t = type(x)
    has_prop = hasattr(x, "name")
    val = getattr(x, "name", "default")
"""
        ir = build_ir(code)
        func = ir.functions[0]
        self.assertIsInstance(func.body[0].value, IRIsInstance)

        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("instanceof Integer", java)
        self.assertIn("typeof x === 'number'", js)
        self.assertIn("typeof x === 'function'", js)

    def test_string_operations(self):
        code = """
def process_text(s):
    left = s.lstrip()
    right = s.rstrip()
    c = s.count("a")
    pos = s.find("target")
"""
        java = self.engine.translate(code, "java")
        cpp = self.engine.translate(code, "cpp")
        js = self.engine.translate(code, "javascript")

        self.assertIn("trimStart()", js)
        self.assertIn("trimEnd()", js)
        self.assertIn(".indexOf(", js)

        self.assertIn("replaceAll(\"^\\\\s+\"", java)
        self.assertIn("replaceAll(\"\\\\s+$\"", java)

    def test_starred_arguments_lowering(self):
        code = """
def invoke(fn, items, options):
    return fn(*items, **options)
"""
        ir = build_ir(code)
        call_node = ir.functions[0].body[0].value
        self.assertTrue(any(isinstance(a, IRStarred) for a in call_node.arguments))

        js = self.engine.translate(code, "javascript")
        self.assertIn("...items", js)
        self.assertIn("...options", js)


if __name__ == "__main__":
    unittest.main()
