"""
Rosetta AI - C++ Target Code Generator Tests (Phase 7)
------------------------------------------------------
Verifies Python/IR to C++ translation:
- Free functions, parameter & return type resolution
- Assignment, local type inference, and reassignment scope tracking
- Constant literal mapping (numbers, strings, booleans, nullptr)
- Binary and unary operator translation
- Control flow structures (if/else, while, for range-loops, and range-based for)
- Function calls and print() / len() mappings
- Collections support (std::vector and std::map)
- Automatic include management (<iostream>, <string>, <vector>, <map>)
- Keyword collision avoidance
- TranslationEngine integration with 'cpp' and 'c++' alias
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
    CppGenerator,
    TranslationEngine,
    TranslationError,
    UnsupportedIRNodeError,
)


class TestCppGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = CppGenerator()
        self.engine = TranslationEngine()

    def test_1_simple_function_add(self):
        """
        Test 1 — Simple function:
        def add(a: int, b: int) -> int: return a + b
        """
        func = IRFunction(
            name="add",
            parameters=["a", "b"],
            parameter_types={"a": "int", "b": "int"},
            return_type="int",
            body=[
                IRReturn(
                    value=IRBinaryOperation(left=IRName("a"), operator="+", right=IRName("b"))
                )
            ],
        )
        output = self.generator.generate(func)

        self.assertIn("int add(int a, int b) {", output)
        self.assertIn("return a + b;", output)
        self.assertTrue(output.strip().endswith("}"))

    def test_2_assignment(self):
        """
        Test 2 — Assignment & Variable Declarations:
        x = 10 -> int x = 10;
        count: int = 5 -> int count = 5;
        y: int -> int y;
        """
        assign_inferred = IRAssignment("x", IRConstant(10, "int"))
        self.assertEqual(self.generator.generate(assign_inferred), "int x = 10;")

        gen2 = CppGenerator()
        assign_typed = IRAssignment("count", IRConstant(5, "int"), var_type="int")
        self.assertEqual(gen2.generate(assign_typed), "int count = 5;")

        gen3 = CppGenerator()
        uninit_var = IRAssignment("y", None, var_type="int")
        self.assertEqual(gen3.generate(uninit_var), "int y;")

    def test_3_local_type_inference(self):
        """
        Test 3 — Local type inference:
        int, double, std::string, bool.
        """
        gen = CppGenerator()

        self.assertEqual(gen.generate(IRAssignment("count", IRConstant(42, "int"))), "int count = 42;")
        self.assertEqual(gen.generate(IRAssignment("price", IRConstant(19.99, "float"))), "double price = 19.99;")
        self.assertEqual(gen.generate(IRAssignment("title", IRConstant("Rosetta", "str"))), 'std::string title = "Rosetta";')
        self.assertEqual(gen.generate(IRAssignment("flag", IRConstant(True, "bool"))), "bool flag = true;")

    def test_4_reassignment_no_redeclaration(self):
        """
        Test 4 — Reassignment:
        Verify variables are not redeclared on reassignment in the same scope.
        """
        gen = CppGenerator()
        gen.reset_state()

        first = gen.generate(IRAssignment("total", IRConstant(0, "int")))
        self.assertEqual(first, "int total = 0;")

        second = gen.generate(IRAssignment("total", IRConstant(100, "int")))
        self.assertEqual(second, "total = 100;")

    def test_5_parameter_assignment_no_redeclaration(self):
        """
        Test 5 — Parameter assignment:
        Verify parameters in function header are not redeclared in function body.
        """
        func = IRFunction(
            name="resetParam",
            parameters=["x"],
            parameter_types={"x": "int"},
            return_type="void",
            body=[
                IRAssignment(target="x", value=IRConstant(0, "int"))
            ],
        )
        output = self.generator.generate(func)

        self.assertIn("void resetParam(int x) {", output)
        self.assertIn("x = 0;", output)
        self.assertNotIn("int x = 0;", output)

    def test_6_constants(self):
        """
        Test 6 — Constants:
        10, 3.14, 'hello', True, False, None -> nullptr.
        """
        self.assertEqual(self.generator.generate(IRConstant(10, "int")), "10")
        self.assertEqual(self.generator.generate(IRConstant(3.14, "float")), "3.14")
        self.assertEqual(self.generator.generate(IRConstant("hello", "str")), '"hello"')
        self.assertEqual(self.generator.generate(IRConstant(True, "bool")), "true")
        self.assertEqual(self.generator.generate(IRConstant(False, "bool")), "false")
        self.assertEqual(self.generator.generate(IRConstant(None, "None")), "nullptr")

    def test_7_binary_operators(self):
        """
        Test 7 — Binary operators:
        +, -, *, /, %, ==, !=, <, <=, >, >=, &&, ||.
        """
        cases = [
            ("+", "+"),
            ("-", "-"),
            ("*", "*"),
            ("/", "/"),
            ("%", "%"),
            ("==", "=="),
            ("!=", "!="),
            ("<", "<"),
            ("<=", "<="),
            (">", ">"),
            (">=", ">="),
            ("and", "&&"),
            ("or", "||"),
        ]

        for ir_op, expected_cpp_op in cases:
            bin_op = IRBinaryOperation(left=IRName("a"), operator=ir_op, right=IRName("b"))
            output = self.generator.generate(bin_op)
            self.assertEqual(output, f"a {expected_cpp_op} b")

    def test_8_unary_operators(self):
        """
        Test 8 — Unary operators:
        not -> !, - -> -
        """
        not_op = IRUnaryOperation(operator="not", operand=IRName("isValid"))
        self.assertEqual(self.generator.generate(not_op), "!isValid")

        neg_op = IRUnaryOperation(operator="-", operand=IRName("count"))
        self.assertEqual(self.generator.generate(neg_op), "-count")

    def test_9_if_else(self):
        """
        Test 9 — If / Else:
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

    def test_10_while_loop(self):
        """
        Test 10 — While loop:
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

    def test_11_for_range_loop(self):
        """
        Test 11 — For/range loop:
        for i in range(10): ...
        for i in range(1, 10): ...
        """
        for_single_arg = IRFor(
            variable="i",
            iterable=IRFunctionCall("range", [IRConstant(10, "int")]),
            body=[
                IRExpressionStatement(IRFunctionCall("print", [IRName("i")]))
            ],
        )
        output1 = self.generator.generate(for_single_arg)
        self.assertIn("for (int i = 0; i < 10; ++i) {", output1)
        self.assertIn("std::cout << i << std::endl;", output1)

        gen2 = CppGenerator()
        for_two_args = IRFor(
            variable="i",
            iterable=IRFunctionCall("range", [IRConstant(1, "int"), IRConstant(10, "int")]),
            body=[
                IRExpressionStatement(IRFunctionCall("print", [IRName("i")]))
            ],
        )
        output2 = gen2.generate(for_two_args)
        self.assertIn("for (int i = 1; i < 10; ++i) {", output2)

    def test_12_for_in_iterable(self):
        """
        Test 12 — Range-based for loop:
        for item in items: ...
        """
        for_node = IRFor(
            variable="item",
            iterable=IRName("items"),
            body=[
                IRExpressionStatement(IRFunctionCall("print", [IRName("item")]))
            ],
        )
        output = self.generator.generate(for_node)
        self.assertIn("for (const auto& item : items) {", output)

    def test_13_function_call(self):
        """
        Test 13 — Function call:
        calculateTotal(price, tax)
        len(items)
        """
        call = IRFunctionCall("calculateTotal", [IRName("price"), IRName("tax")])
        self.assertEqual(self.generator.generate(call), "calculateTotal(price, tax)")

        len_call = IRFunctionCall("len", [IRName("items")])
        self.assertEqual(self.generator.generate(len_call), "items.size()")

    def test_14_print_mapping(self):
        """
        Test 14 — print mapping:
        print(value) -> std::cout << value << std::endl; and <iostream> included.
        """
        print_stmt = IRExpressionStatement(IRFunctionCall("print", [IRName("message")]))
        output = self.generator.generate(print_stmt)

        self.assertEqual(output, "std::cout << message << std::endl;")
        self.assertIn("#include <iostream>", self.generator._required_includes)

    def test_15_string_support(self):
        """
        Test 15 — String support:
        std::string and #include <string>.
        """
        assign = IRAssignment("greeting", IRConstant("Hello, C++", "str"))
        prog = IRProgram(statements=[assign])
        output = self.generator.generate(prog)

        self.assertIn("#include <string>", output)
        self.assertIn('std::string greeting = "Hello, C++";', output)

    def test_16_collections_support(self):
        """
        Test 16 — Collections:
        std::vector and std::map with <vector> and <map> includes.
        """
        prog = IRProgram(
            statements=[
                IRAssignment("nums", IRList([IRConstant(1, "int"), IRConstant(2, "int")])),
                IRAssignment("lookup", IRDict([IRConstant("k", "str")], [IRConstant(42, "int")])),
            ]
        )
        output = self.generator.generate(prog)

        self.assertIn("#include <map>", output)
        self.assertIn("#include <vector>", output)
        self.assertIn("std::vector<int> nums = std::vector<int>{1, 2};", output)
        self.assertIn('std::map<std::string, int> lookup = std::map<std::string, int>{{"k", 42}};', output)

    def test_17_translation_engine_integration_and_alias(self):
        """
        Test 17 — TranslationEngine integration:
        engine.translate(ir_prog, 'cpp') and 'c++'.
        """
        source_python = """def multiply(a: int, b: int) -> int:
    return a * b
"""
        ir_prog = build_ir(source_python)

        code_cpp = self.engine.translate(ir_prog, "cpp")
        self.assertIn("int multiply(int a, int b) {", code_cpp)
        self.assertIn("return a * b;", code_cpp)

        code_cplusplus = self.engine.translate(ir_prog, "c++")
        self.assertEqual(code_cpp, code_cplusplus)

    def test_18_unsupported_construct_behavior(self):
        """
        Test 18 — Unsupported construct:
        Unrecognized custom IR node raises UnsupportedIRNodeError cleanly.
        """
        class UnknownCustomNode(IRNode):
            pass

        with self.assertRaises(UnsupportedIRNodeError) as ctx:
            self.generator.generate(UnknownCustomNode())

        self.assertIn("UnknownCustomNode", str(ctx.exception))

    def test_19_keyword_collision_sanitization(self):
        """
        Test 19 — Keyword collision sanitization:
        Avoid collision with C++ keywords like class, template, namespace.
        """
        func = IRFunction(
            name="template",
            parameters=["class", "namespace"],
            parameter_types={"class": "int", "namespace": "int"},
            return_type="int",
            body=[
                IRReturn(
                    value=IRBinaryOperation(left=IRName("class"), operator="+", right=IRName("namespace"))
                )
            ],
        )
        output = self.generator.generate(func)

        self.assertIn("int template_(int class_, int namespace_) {", output)
        self.assertIn("return class_ + namespace_;", output)

    def test_20_program_with_top_level_statements(self):
        """
        Test 20 — Program structuring:
        Top-level statements wrapped in int main() with includes placed at the top.
        """
        prog = IRProgram(
            functions=[
                IRFunction(
                    name="greet",
                    parameters=[],
                    return_type="void",
                    body=[
                        IRExpressionStatement(IRFunctionCall("print", [IRConstant("Hello", "str")]))
                    ],
                )
            ],
            statements=[
                IRExpressionStatement(IRFunctionCall("greet", []))
            ],
        )
        output = self.generator.generate(prog)

        self.assertIn("#include <iostream>", output)
        self.assertIn("#include <string>", output)
        self.assertIn("void greet() {", output)
        self.assertIn("int main() {", output)
        self.assertIn("greet();", output)
        self.assertIn("return 0;", output)


if __name__ == "__main__":
    unittest.main()
