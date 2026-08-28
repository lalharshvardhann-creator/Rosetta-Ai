"""
Unit tests for Rosetta AI Java Target Code Generator (Phases 6 & 6.2).
Verifies IR to Java translation, type inference, scope tracking, collection support,
import deduplication, and invalid Object operation prevention.
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
    JavaGenerator,
    TranslationEngine,
    TranslationError,
    UnsupportedIRNodeError,
)


class TestJavaGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = JavaGenerator()
        self.engine = TranslationEngine()

    def test_1_simple_function_add(self):
        """
        Test 1 — Simple function:
        def add(a, b):
            return a + b
        """
        func_node = IRFunction(
            name="add",
            parameters=["a", "b"],
            body=[
                IRReturn(
                    value=IRBinaryOperation(
                        left=IRName(name="a"),
                        operator="+",
                        right=IRName(name="b"),
                    )
                )
            ],
        )
        output = self.generator.generate(func_node)

        self.assertIn("public static Object add(Object a, Object b)", output)
        self.assertIn("return a + b;", output)
        self.assertTrue(output.strip().endswith("}"))

    def test_2_assignment_and_inference(self):
        """
        Test 2 — Assignment & Inferred Type:
        x = 10 -> int x = 10;
        """
        assign_node = IRAssignment(
            target="x",
            value=IRConstant(value=10, data_type="int"),
        )
        output = self.generator.generate(assign_node)
        self.assertEqual(output, "int x = 10;")

        typed_assign = IRAssignment(
            target="count",
            value=IRConstant(value=5, data_type="int"),
            var_type="int",
        )
        typed_output = self.generator.generate(typed_assign)
        self.assertEqual(typed_output, "int count = 5;")

    def test_3_constants(self):
        """
        Test 3 — Constants:
        Verify 10, 3.14, 'hello', true, false, null.
        """
        int_const = IRConstant(value=10, data_type="int")
        float_const = IRConstant(value=3.14, data_type="float")
        str_const = IRConstant(value="hello", data_type="str")
        bool_true = IRConstant(value=True, data_type="bool")
        bool_false = IRConstant(value=False, data_type="bool")
        none_const = IRConstant(value=None, data_type="None")

        self.assertEqual(self.generator.generate(int_const), "10")
        self.assertEqual(self.generator.generate(float_const), "3.14")
        self.assertEqual(self.generator.generate(str_const), '"hello"')
        self.assertEqual(self.generator.generate(bool_true), "true")
        self.assertEqual(self.generator.generate(bool_false), "false")
        self.assertEqual(self.generator.generate(none_const), "null")

    def test_4_binary_operations(self):
        """
        Test 4 — Binary operations:
        Verify operators (+, -, *, /, %, ==, !=, <, >, &&, ||) are translated correctly.
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

        for ir_op, expected_java_op in cases:
            bin_op = IRBinaryOperation(
                left=IRName("a"),
                operator=ir_op,
                right=IRName("b"),
            )
            output = self.generator.generate(bin_op)
            self.assertEqual(output, f"a {expected_java_op} b")

    def test_5_if_else(self):
        """
        Test 5 — If / Else:
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

    def test_6_while_loop(self):
        """
        Test 6 — While loop:
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

    def test_7_function_call(self):
        """
        Test 7 — Function call:
        calculateTotal(price, 0.08)
        """
        call_node = IRFunctionCall(
            name="calculateTotal",
            arguments=[IRName("price"), IRConstant(value=0.08, data_type="float")],
        )
        output = self.generator.generate(call_node)
        self.assertEqual(output, "calculateTotal(price, 0.08)")

    def test_8_print_mapping(self):
        """
        Test 8 — print() mapping:
        print(message) -> System.out.println(message);
        """
        print_call = IRFunctionCall(
            name="print",
            arguments=[IRName("message")],
        )
        stmt_node = IRExpressionStatement(expression=print_call)
        output = self.generator.generate(stmt_node)

        self.assertEqual(output, "System.out.println(message);")

    def test_9_translation_engine_integration(self):
        """
        Test 9 — TranslationEngine integration:
        engine.translate(ir_program, 'java')
        """
        source_python = """def multiply(a, b):
    return a * b
"""
        ir_prog = build_ir(source_python)
        java_code = self.engine.translate(ir_prog, "java")

        self.assertIn("public class Main {", java_code)
        self.assertIn("public static Object multiply(Object a, Object b) {", java_code)
        self.assertIn("return a * b;", java_code)

    def test_10_unsupported_construct_behavior(self):
        """
        Test 10 — Unsupported construct behavior:
        Unrecognized custom IR node raises UnsupportedIRNodeError cleanly.
        """
        class UnrecognizedCustomIR(IRNode):
            pass

        unsupported = UnrecognizedCustomIR()
        with self.assertRaises(UnsupportedIRNodeError) as ctx:
            self.generator.generate(unsupported)

        self.assertIn("UnrecognizedCustomIR", str(ctx.exception))

    def test_11_local_variable_inference_types(self):
        """Verify type inference for int, double, String, boolean literals."""
        gen = JavaGenerator()

        assign_int = IRAssignment("count", IRConstant(42, "int"))
        self.assertEqual(gen.generate(assign_int), "int count = 42;")

        assign_double = IRAssignment("price", IRConstant(19.99, "float"))
        self.assertEqual(gen.generate(assign_double), "double price = 19.99;")

        assign_str = IRAssignment("title", IRConstant("Rosetta", "str"))
        self.assertEqual(gen.generate(assign_str), 'String title = "Rosetta";')

        assign_bool = IRAssignment("isValid", IRConstant(True, "bool"))
        self.assertEqual(gen.generate(assign_bool), "boolean isValid = true;")

    def test_12_scope_reassignment_no_redeclaration(self):
        """Verify that reassigning a variable in the same scope does not redeclare its type."""
        gen = JavaGenerator()
        gen.reset_state()

        first_assign = IRAssignment("total", IRConstant(0, "int"))
        self.assertEqual(gen.generate(first_assign), "int total = 0;")

        second_assign = IRAssignment("total", IRConstant(100, "int"))
        self.assertEqual(gen.generate(second_assign), "total = 100;")

    def test_13_parameter_assignment_no_redeclaration(self):
        """Verify parameters declared in method header are not redeclared in method body."""
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

        self.assertIn("public static void resetParam(int x) {", output)
        self.assertIn("x = 0;", output)
        self.assertNotIn("int x = 0;", output)

    def test_14_collections_list_generation(self):
        """Verify list generation produces Arrays.asList and registers List imports."""
        list_node = IRList(elements=[IRConstant(1, "int"), IRConstant(2, "int"), IRConstant(3, "int")])
        assign_node = IRAssignment("numbers", list_node)
        output = self.generator.generate(assign_node)

        self.assertEqual(output, "List<Object> numbers = Arrays.asList(1, 2, 3);")
        self.assertIn("import java.util.List;", self.generator._required_imports)
        self.assertIn("import java.util.Arrays;", self.generator._required_imports)

    def test_15_collections_dict_generation(self):
        """Verify dictionary generation produces Map.of and registers Map imports."""
        dict_node = IRDict(
            keys=[IRConstant("alice", "str"), IRConstant("bob", "str")],
            values=[IRConstant(95, "int"), IRConstant(88, "int")],
        )
        assign_node = IRAssignment("scores", dict_node)
        output = self.generator.generate(assign_node)

        self.assertEqual(output, 'Map<Object, Object> scores = Map.of("alice", 95, "bob", 88);')
        self.assertIn("import java.util.Map;", self.generator._required_imports)

    def test_16_import_deduplication(self):
        """Verify imports in IRProgram are deduplicated and sorted before the class."""
        prog = IRProgram(
            imports=[
                IRImport(module="java.util", names=["List"]),
                IRImport(module="java.util", names=["List"]),
                IRImport(module="java.io", names=["File"]),
            ],
            statements=[
                IRAssignment("items", IRList(elements=[IRConstant("a", "str")]))
            ],
        )
        output = self.generator.generate(prog)

        class_idx = output.find("public class Main")
        import_list_idx = output.find("import java.util.List;")
        import_file_idx = output.find("import java.io.*;")

        self.assertTrue(import_list_idx < class_idx)
        self.assertTrue(import_file_idx < class_idx)

        self.assertEqual(output.count("import java.util.List;"), 1)

    def test_17_invalid_object_operation_prevention(self):
        """Verify primitive operations on explicit Object types raise TranslationError."""
        gen = JavaGenerator()
        invalid_sub = IRBinaryOperation(
            left=IRVariable(name="objA", var_type="Object"),
            operator="-",
            right=IRVariable(name="objB", var_type="Object"),
        )

        with self.assertRaises(TranslationError) as ctx:
            gen.generate(invalid_sub)

        self.assertIn("cannot be applied to type 'Object'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
