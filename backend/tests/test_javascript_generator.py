"""
Rosetta AI - JavaScript Target Code Generator Tests (Phase 8)
-------------------------------------------------------------
Verifies Python/IR to JavaScript translation:
- Free functions, async functions, parameters & return statements
- Variable declarations (let), reassignment without redeclaration
- Parameter scope tracking (no redeclaration of parameters)
- Constant literal mappings (numbers, strings, booleans, null)
- Operator mappings with strict equality (===, !==) and logical operators
- Control flow structures (if/else, while, numeric range loops, for...of loops)
- Built-in mappings (print -> console.log, len -> .length)
- Collections (native arrays and object literals)
- Classes with constructor and methods
- Top-level script-level statement execution (no main() wrapper)
- Keyword collision avoidance (class_, function_, etc.)
- TranslationEngine integration and 'js' alias
- Unsupported construct error handling
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import (
    IRAssignment,
    IRBinaryOperation,
    IRClass,
    IRConstant,
    IRDict,
    IRExpressionStatement,
    IRFor,
    IRFunction,
    IRFunctionCall,
    IRIf,
    IRImport,
    IRList,
    IRName,
    IRNode,
    IRProgram,
    IRReturn,
    IRUnaryOperation,
    IRVariable,
    IRWhile,
    build_ir,
)
from app.translation import (
    JavaScriptGenerator,
    TranslationEngine,
    TranslationError,
    UnsupportedIRNodeError,
)


class TestJavaScriptGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = JavaScriptGenerator()
        self.engine = TranslationEngine()

    def test_1_simple_function(self):
        """
        Test 1 — Simple function:
        def add(a, b): return a + b
        """
        func = IRFunction(
            name="add",
            parameters=["a", "b"],
            body=[
                IRReturn(
                    value=IRBinaryOperation(left=IRName("a"), operator="+", right=IRName("b"))
                )
            ],
        )
        output = self.generator.generate(func)

        self.assertIn("function add(a, b) {", output)
        self.assertIn("return a + b;", output)
        self.assertTrue(output.strip().endswith("}"))

    def test_2_function_parameters(self):
        """
        Test 2 — Function parameters:
        Verify parameter names are formatted correctly without types.
        """
        func = IRFunction(
            name="compute",
            parameters=["x", "y", "z"],
            body=[IRReturn(value=IRName("x"))],
        )
        output = self.generator.generate(func)
        self.assertIn("function compute(x, y, z) {", output)

    def test_3_return_statement(self):
        """
        Test 3 — Return statement:
        return 42; and bare return;
        """
        ret_val = IRReturn(value=IRConstant(42, "int"))
        self.assertEqual(self.generator.generate(ret_val), "return 42;")

        ret_bare = IRReturn(value=None)
        self.assertEqual(self.generator.generate(ret_bare), "return;")

    def test_4_integer_constants(self):
        """
        Test 4 — Integer constants:
        0, 10, -5 -> 0, 10, -5
        """
        self.assertEqual(self.generator.generate(IRConstant(0, "int")), "0")
        self.assertEqual(self.generator.generate(IRConstant(10, "int")), "10")
        self.assertEqual(self.generator.generate(IRConstant(-5, "int")), "-5")

    def test_5_float_constants(self):
        """
        Test 5 — Float constants:
        3.14, 0.001
        """
        self.assertEqual(self.generator.generate(IRConstant(3.14, "float")), "3.14")
        self.assertEqual(self.generator.generate(IRConstant(0.001, "float")), "0.001")

    def test_6_string_constants(self):
        """
        Test 6 — String constants:
        Properly escaped JavaScript strings.
        """
        self.assertEqual(self.generator.generate(IRConstant("hello", "str")), '"hello"')
        self.assertEqual(self.generator.generate(IRConstant('hello "world"', "str")), '"hello \\"world\\""')
        self.assertEqual(self.generator.generate(IRConstant("line1\nline2", "str")), '"line1\\nline2"')

    def test_7_true_false_none(self):
        """
        Test 7 — True / False / None:
        True -> true, False -> false, None -> null
        """
        self.assertEqual(self.generator.generate(IRConstant(True, "bool")), "true")
        self.assertEqual(self.generator.generate(IRConstant(False, "bool")), "false")
        self.assertEqual(self.generator.generate(IRConstant(None, "None")), "null")

    def test_8_variable_declaration(self):
        """
        Test 8 — Variable declaration:
        let x = 10; and let y;
        """
        gen = JavaScriptGenerator()
        assign = IRAssignment("x", IRConstant(10, "int"))
        self.assertEqual(gen.generate(assign), "let x = 10;")

        gen2 = JavaScriptGenerator()
        uninit = IRAssignment("y", None)
        self.assertEqual(gen2.generate(uninit), "let y;")

    def test_9_variable_reassignment(self):
        """
        Test 9 — Variable reassignment:
        First assignment uses let, subsequent reassignment in same scope does not.
        """
        gen = JavaScriptGenerator()
        first = gen.generate(IRAssignment("count", IRConstant(0, "int")))
        self.assertEqual(first, "let count = 0;")

        second = gen.generate(IRAssignment("count", IRConstant(1, "int")))
        self.assertEqual(second, "count = 1;")

    def test_10_parameter_redeclaration_prevention(self):
        """
        Test 10 — Parameter redeclaration prevention:
        Function parameters must not be redeclared with 'let' in the body.
        """
        func = IRFunction(
            name="update",
            parameters=["value"],
            body=[
                IRAssignment(target="value", value=IRConstant(100, "int"))
            ],
        )
        output = self.generator.generate(func)

        self.assertIn("function update(value) {", output)
        self.assertIn("value = 100;", output)
        self.assertNotIn("let value = 100;", output)

    def test_11_binary_operators(self):
        """
        Test 11 — Binary operators:
        +, -, *, /, %, <, <=, >, >=, &&, ||
        """
        cases = [
            ("+", "+"),
            ("-", "-"),
            ("*", "*"),
            ("/", "/"),
            ("%", "%"),
            ("<", "<"),
            ("<=", "<="),
            (">", ">"),
            (">=", ">="),
            ("and", "&&"),
            ("or", "||"),
        ]

        for ir_op, expected_js_op in cases:
            bin_op = IRBinaryOperation(left=IRName("a"), operator=ir_op, right=IRName("b"))
            output = self.generator.generate(bin_op)
            self.assertEqual(output, f"a {expected_js_op} b")

    def test_12_strict_equality_mapping(self):
        """
        Test 12 — Strict equality mapping:
        == -> === and != -> !==
        """
        eq_op = IRBinaryOperation(left=IRName("a"), operator="==", right=IRName("b"))
        self.assertEqual(self.generator.generate(eq_op), "a === b")

        neq_op = IRBinaryOperation(left=IRName("a"), operator="!=", right=IRName("b"))
        self.assertEqual(self.generator.generate(neq_op), "a !== b")

    def test_13_unary_operators(self):
        """
        Test 13 — Unary operators:
        not -> !, - -> -
        """
        not_op = IRUnaryOperation(operator="not", operand=IRName("isValid"))
        self.assertEqual(self.generator.generate(not_op), "!isValid")

        neg_op = IRUnaryOperation(operator="-", operand=IRName("num"))
        self.assertEqual(self.generator.generate(neg_op), "-num")

    def test_14_if_else(self):
        """
        Test 14 — If / else:
        if x > 10: return x else: return 0
        """
        if_node = IRIf(
            condition=IRBinaryOperation(left=IRName("x"), operator=">", right=IRConstant(10, "int")),
            then_body=[IRReturn(value=IRName("x"))],
            else_body=[IRReturn(value=IRConstant(0, "int"))],
        )
        output = self.generator.generate(if_node)

        self.assertIn("if (x > 10) {", output)
        self.assertIn("return x;", output)
        self.assertIn("} else {", output)
        self.assertIn("return 0;", output)

    def test_15_while_loop(self):
        """
        Test 15 — While loop:
        while x < 10: x = x + 1
        """
        while_node = IRWhile(
            condition=IRBinaryOperation(left=IRName("x"), operator="<", right=IRConstant(10, "int")),
            body=[
                IRAssignment(
                    target="x",
                    value=IRBinaryOperation(left=IRName("x"), operator="+", right=IRConstant(1, "int")),
                )
            ],
        )
        output = self.generator.generate(while_node)

        self.assertIn("while (x < 10) {", output)
        self.assertIn("x = x + 1;", output)

    def test_16_for_range_loop(self):
        """
        Test 16 — Range loops:
        range(10), range(1, 10), and range(0, 10, 2)
        """
        for_1 = IRFor(
            variable="i",
            iterable=IRFunctionCall("range", [IRConstant(10, "int")]),
            body=[IRExpressionStatement(IRFunctionCall("print", [IRName("i")]))],
        )
        out1 = self.generator.generate(for_1)
        self.assertIn("for (let i = 0; i < 10; i++) {", out1)
        self.assertIn("console.log(i);", out1)

        gen2 = JavaScriptGenerator()
        for_2 = IRFor(
            variable="i",
            iterable=IRFunctionCall("range", [IRConstant(1, "int"), IRConstant(10, "int")]),
            body=[IRExpressionStatement(IRFunctionCall("print", [IRName("i")]))],
        )
        out2 = gen2.generate(for_2)
        self.assertIn("for (let i = 1; i < 10; i++) {", out2)

        gen3 = JavaScriptGenerator()
        for_3 = IRFor(
            variable="i",
            iterable=IRFunctionCall("range", [IRConstant(0, "int"), IRConstant(10, "int"), IRConstant(2, "int")]),
            body=[IRExpressionStatement(IRFunctionCall("print", [IRName("i")]))],
        )
        out3 = gen3.generate(for_3)
        self.assertIn("for (let i = 0; i < 10; i += 2) {", out3)

    def test_17_collection_iteration(self):
        """
        Test 17 — Collection iteration:
        for item in items: print(item) -> for (const item of items)
        """
        for_of = IRFor(
            variable="item",
            iterable=IRName("items"),
            body=[IRExpressionStatement(IRFunctionCall("print", [IRName("item")]))],
        )
        output = self.generator.generate(for_of)
        self.assertIn("for (const item of items) {", output)
        self.assertIn("console.log(item);", output)

    def test_18_function_call(self):
        """
        Test 18 — Function call:
        calculateTotal(price, 0.08)
        """
        call = IRFunctionCall(
            name="calculateTotal",
            arguments=[IRName("price"), IRConstant(0.08, "float")],
        )
        self.assertEqual(self.generator.generate(call), "calculateTotal(price, 0.08)")

    def test_19_print_mapping(self):
        """
        Test 19 — print() -> console.log():
        Single and multiple arguments.
        """
        p1 = IRExpressionStatement(IRFunctionCall("print", [IRName("msg")]))
        self.assertEqual(self.generator.generate(p1), "console.log(msg);")

        p2 = IRExpressionStatement(IRFunctionCall("print", [IRName("a"), IRName("b")]))
        self.assertEqual(self.generator.generate(p2), "console.log(a, b);")

    def test_20_len_mapping(self):
        """
        Test 20 — len(x) -> x.length
        """
        len_call = IRFunctionCall("len", [IRName("items")])
        self.assertEqual(self.generator.generate(len_call), "items.length")

    def test_21_list_array_generation(self):
        """
        Test 21 — List -> JavaScript array:
        [1, 2, 3] -> [1, 2, 3]
        """
        arr_node = IRList([IRConstant(1, "int"), IRConstant(2, "int"), IRConstant(3, "int")])
        self.assertEqual(self.generator.generate(arr_node), "[1, 2, 3]")

    def test_22_dict_object_generation(self):
        """
        Test 22 — Dict -> JavaScript object:
        {"name": "Alice", "age": 20}
        """
        dict_node = IRDict(
            keys=[IRConstant("name", "str"), IRConstant("age", "str")],
            values=[IRConstant("Alice", "str"), IRConstant(20, "int")],
        )
        output = self.generator.generate(dict_node)
        self.assertEqual(output, '{"name": "Alice", "age": 20}')

    def test_23_translation_engine_integration(self):
        """
        Test 23 — TranslationEngine integration:
        engine.translate(ir_prog, 'javascript')
        """
        code = """def multiply(a, b):
    return a * b
"""
        ir_prog = build_ir(code)
        js_code = self.engine.translate(ir_prog, "javascript")

        self.assertIn("function multiply(a, b) {", js_code)
        self.assertIn("return a * b;", js_code)

    def test_24_js_alias_support(self):
        """
        Test 24 — 'js' alias support:
        engine.translate(ir_prog, 'js')
        """
        code = """def add(a, b):
    return a + b
"""
        ir_prog = build_ir(code)
        js_code = self.engine.translate(ir_prog, "js")
        self.assertIn("function add(a, b) {", js_code)

    def test_25_unsupported_ir_node_error(self):
        """
        Test 25 — Unsupported IR node:
        Unknown node raises UnsupportedIRNodeError cleanly.
        """
        class UnknownCustomNode(IRNode):
            pass

        with self.assertRaises(UnsupportedIRNodeError) as ctx:
            self.generator.generate(UnknownCustomNode())

        self.assertIn("UnknownCustomNode", str(ctx.exception))

    def test_26_reserved_keyword_handling(self):
        """
        Test 26 — Reserved keyword handling:
        Identifier collisions with JS keywords (function, class, return, let) are sanitized.
        """
        func = IRFunction(
            name="function",
            parameters=["class", "let", "return"],
            body=[
                IRReturn(
                    value=IRBinaryOperation(left=IRName("class"), operator="+", right=IRName("let"))
                )
            ],
        )
        output = self.generator.generate(func)

        self.assertIn("function function_(class_, let_, return_) {", output)
        self.assertIn("return class_ + let_;", output)

    def test_27_top_level_statements(self):
        """
        Test 27 — Top-level statements:
        Emitted directly at module level without main() or class wrapper.
        """
        prog = IRProgram(
            functions=[
                IRFunction(
                    name="greet",
                    parameters=["name"],
                    body=[
                        IRExpressionStatement(
                            IRFunctionCall("print", [
                                IRBinaryOperation(left=IRConstant("Hello, ", "str"), operator="+", right=IRName("name"))
                            ])
                        )
                    ],
                )
            ],
            statements=[
                IRExpressionStatement(IRFunctionCall("greet", [IRConstant("Rosetta", "str")]))
            ],
        )
        output = self.generator.generate(prog)

        self.assertIn("function greet(name) {", output)
        self.assertIn('console.log("Hello, " + name);', output)
        self.assertIn('greet("Rosetta");', output)
        self.assertNotIn("function main()", output)
        self.assertNotIn("class Main", output)

    def test_28_async_function_support(self):
        """
        Test 28 — Async function support:
        async def fetch_data() -> async function fetchData()
        """
        func = IRFunction(
            name="fetchData",
            parameters=["url"],
            is_async=True,
            body=[
                IRReturn(value=IRName("url"))
            ],
        )
        output = self.generator.generate(func)

        self.assertIn("async function fetchData(url) {", output)
        self.assertIn("return url;", output)

    def test_29_class_and_methods(self):
        """
        Test 29 — ES6 Class and methods:
        class Person extends Entity with constructor and methods.
        """
        cls_node = IRClass(
            name="Person",
            bases=["Entity"],
            methods=[
                IRFunction(
                    name="__init__",
                    parameters=["self", "name"],
                    body=[
                        IRAssignment("this.name", IRName("name"))
                    ],
                ),
                IRFunction(
                    name="getName",
                    parameters=["self"],
                    body=[
                        IRReturn(IRName("this.name"))
                    ],
                ),
            ],
        )
        output = self.generator.generate(cls_node)

        self.assertIn("class Person extends Entity {", output)
        self.assertIn("constructor(name) {", output)
        self.assertIn("getName() {", output)


if __name__ == "__main__":
    unittest.main()
