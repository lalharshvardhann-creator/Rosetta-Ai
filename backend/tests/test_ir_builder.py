"""
Unit tests for Rosetta AI Intermediate Representation (IR) Builder and Nodes.
Verifies AST to IR translation and JSON serialization.
"""

import json
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
    IRExpressionStatement,
    IRFor,
    IRFunction,
    IRFunctionCall,
    IRIf,
    IRImport,
    IRName,
    IRProgram,
    IRReturn,
    IRUnaryOperation,
    IRWhile,
    build_ir,
)


class TestIRBuilder(unittest.TestCase):

    def test_1_function_add(self):
        """
        Test 1:
        Input:
            def add(a, b):
                return a + b
        Verify:
            - one function exists
            - function name is "add"
            - parameters are ["a", "b"]
            - function body contains a return
            - return contains a binary operation
            - operator is "+"
        """
        code = """def add(a, b):
    return a + b
"""
        program = build_ir(code)

        self.assertEqual(len(program.functions), 1)
        func = program.functions[0]

        self.assertEqual(func.name, "add")

        self.assertEqual(func.parameters, ["a", "b"])

        self.assertEqual(len(func.body), 1)
        self.assertIsInstance(func.body[0], IRReturn)
        return_node = func.body[0]

        self.assertIsInstance(return_node.value, IRBinaryOperation)
        bin_op = return_node.value

        self.assertEqual(bin_op.operator, "+")
        self.assertIsInstance(bin_op.left, IRName)
        self.assertEqual(bin_op.left.name, "a")
        self.assertIsInstance(bin_op.right, IRName)
        self.assertEqual(bin_op.right.name, "b")

    def test_2_assignment(self):
        """
        Test 2:
        Input:
            x = 10
        Verify:
            - assignment exists
            - target is "x"
            - value is the integer constant 10
        """
        code = "x = 10"
        program = build_ir(code)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(program.statements[0], IRAssignment)

        assignment = program.statements[0]
        self.assertEqual(assignment.target, "x")
        self.assertIsInstance(assignment.value, IRConstant)
        self.assertEqual(assignment.value.value, 10)
        self.assertEqual(assignment.value.data_type, "int")

    def test_3_if_else(self):
        """
        Test 3:
        Input:
            if x > 10:
                print(x)
            else:
                print(0)
        Verify:
            - an If node exists
            - condition is represented as a binary operation
            - operator is ">"
            - both then and else bodies are represented
        """
        code = """if x > 10:
    print(x)
else:
    print(0)
"""
        program = build_ir(code)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(program.statements[0], IRIf)

        if_node = program.statements[0]

        self.assertIsInstance(if_node.condition, IRBinaryOperation)
        self.assertEqual(if_node.condition.operator, ">")
        self.assertIsInstance(if_node.condition.left, IRName)
        self.assertEqual(if_node.condition.left.name, "x")
        self.assertIsInstance(if_node.condition.right, IRConstant)
        self.assertEqual(if_node.condition.right.value, 10)

        self.assertEqual(len(if_node.then_body), 1)
        self.assertIsInstance(if_node.then_body[0], IRExpressionStatement)
        then_expr = if_node.then_body[0].expression
        self.assertIsInstance(then_expr, IRFunctionCall)
        self.assertEqual(then_expr.name, "print")

        self.assertEqual(len(if_node.else_body), 1)
        self.assertIsInstance(if_node.else_body[0], IRExpressionStatement)
        else_expr = if_node.else_body[0].expression
        self.assertIsInstance(else_expr, IRFunctionCall)
        self.assertEqual(else_expr.name, "print")

    def test_4_for_loop(self):
        """
        Test 4:
        Input:
            for i in range(10):
                print(i)
        Verify:
            - a For node exists
            - loop variable is "i"
            - iterable is represented
            - loop body is represented
        """
        code = """for i in range(10):
    print(i)
"""
        program = build_ir(code)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(program.statements[0], IRFor)

        for_node = program.statements[0]
        self.assertEqual(for_node.variable, "i")

        self.assertIsInstance(for_node.iterable, IRFunctionCall)
        self.assertEqual(for_node.iterable.name, "range")
        self.assertEqual(len(for_node.iterable.arguments), 1)

        self.assertEqual(len(for_node.body), 1)
        self.assertIsInstance(for_node.body[0], IRExpressionStatement)

    def test_5_while_loop(self):
        """
        Test 5:
        Input:
            while x < 10:
                x = x + 1
        Verify:
            - a While node exists
            - condition is represented
            - body contains an assignment
        """
        code = """while x < 10:
    x = x + 1
"""
        program = build_ir(code)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(program.statements[0], IRWhile)

        while_node = program.statements[0]

        self.assertIsInstance(while_node.condition, IRBinaryOperation)
        self.assertEqual(while_node.condition.operator, "<")

        self.assertEqual(len(while_node.body), 1)
        self.assertIsInstance(while_node.body[0], IRAssignment)
        assign_node = while_node.body[0]
        self.assertEqual(assign_node.target, "x")
        self.assertIsInstance(assign_node.value, IRBinaryOperation)
        self.assertEqual(assign_node.value.operator, "+")

    def test_6_import(self):
        """
        Test 6:
        Input:
            import math
        Verify:
            - import is represented
            - module name is "math"
        """
        code = "import math"
        program = build_ir(code)

        self.assertEqual(len(program.imports), 1)
        import_node = program.imports[0]
        self.assertIsInstance(import_node, IRImport)
        self.assertEqual(import_node.module, "math")
        self.assertIn("math", import_node.names)

    def test_7_serialization_to_json(self):
        """
        Test 7:
        Serialization test confirming that an IR program can be converted
        into a JSON-compatible dictionary without errors.
        """
        code = """import math

class Calculator:
    def compute(self, val):
        if val > 0:
            return val * 2
        return -val

calc = Calculator()
"""
        program = build_ir(code)

        ir_dict = program.to_dict()
        self.assertIsInstance(ir_dict, dict)
        self.assertEqual(ir_dict["node_type"], "IRProgram")

        json_string = json.dumps(ir_dict, indent=2)
        self.assertIsInstance(json_string, str)

        parsed_back = json.loads(json_string)
        self.assertEqual(parsed_back["node_type"], "IRProgram")
        self.assertEqual(len(parsed_back["classes"]), 1)
        self.assertEqual(parsed_back["classes"][0]["name"], "Calculator")

    def test_8_subscript_and_slice(self):
        """Test IRSubscript and IRSlice nodes in IR builder."""
        code = "val = items[0]\npart = text[1:3]"
        program = build_ir(code)

        self.assertEqual(len(program.statements), 2)
        stmt1 = program.statements[0]
        self.assertIsInstance(stmt1, IRAssignment)
        from app.ir.nodes import IRSubscript, IRSlice
        self.assertIsInstance(stmt1.value, IRSubscript)
        self.assertIsInstance(stmt1.value.value, IRName)
        self.assertEqual(stmt1.value.value.name, "items")
        self.assertIsInstance(stmt1.value.slice, IRConstant)
        self.assertEqual(stmt1.value.slice.value, 0)

        stmt2 = program.statements[1]
        self.assertIsInstance(stmt2.value, IRSubscript)
        self.assertIsInstance(stmt2.value.slice, IRSlice)
        self.assertEqual(stmt2.value.slice.lower.value, 1)
        self.assertEqual(stmt2.value.slice.upper.value, 3)

    def test_9_attribute_access(self):
        """Test IRAttribute node in IR builder."""
        code = "name = person.name"
        program = build_ir(code)

        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        from app.ir.nodes import IRAttribute
        self.assertIsInstance(stmt.value, IRAttribute)
        self.assertEqual(stmt.value.attribute, "name")
        self.assertEqual(stmt.value.value.name, "person")


if __name__ == "__main__":
    unittest.main()
