"""
Rosetta AI - JavaScript Runtime Validation Tests (Phase 8)
----------------------------------------------------------
Validates translated JavaScript syntax and executes live tests against Node.js
when available in the environment, or cleanly skips runtime tests if Node.js is not installed.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import (
    IRAssignment,
    IRBinaryOperation,
    IRConstant,
    IRDict,
    IRExpressionStatement,
    IRFor,
    IRFunction,
    IRFunctionCall,
    IRIf,
    IRList,
    IRName,
    IRProgram,
    IRReturn,
    IRWhile,
    build_ir,
)
from app.translation import JavaScriptGenerator, TranslationEngine

NODE_PATH = shutil.which("node")
NODE_AVAILABLE = NODE_PATH is not None


def run_node_exec(js_source: str) -> subprocess.CompletedProcess:
    """
    Helper function to execute JavaScript source code using Node.js.
    Returns the CompletedProcess result (returncode, stdout, stderr).
    """
    if not NODE_AVAILABLE:
        raise RuntimeError("Node.js is not available in this environment.")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "script.js"
        file_path.write_text(js_source, encoding="utf-8")
        return subprocess.run(
            [NODE_PATH, str(file_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )


class TestJavaScriptRuntime(unittest.TestCase):
    """
    Validates JavaScript generation structurally and runs real Node.js execution
    tests when Node.js is detected on the host system.
    """

    def setUp(self):
        self.generator = JavaScriptGenerator()
        self.engine = TranslationEngine()

    def test_function_syntax_structural(self):
        """Verify function generation produces valid JavaScript syntax."""
        func = IRFunction(
            name="add",
            parameters=["a", "b"],
            body=[
                IRReturn(
                    value=IRBinaryOperation(left=IRName("a"), operator="+", right=IRName("b"))
                )
            ],
        )
        prog = IRProgram(functions=[func])
        js_code = self.generator.generate(prog)

        self.assertIn("function add(a, b) {", js_code)
        self.assertIn("return a + b;", js_code)

    def test_if_else_syntax_structural(self):
        """Verify if-else generation produces valid JavaScript syntax."""
        func = IRFunction(
            name="check",
            parameters=["x"],
            body=[
                IRIf(
                    condition=IRBinaryOperation(left=IRName("x"), operator=">", right=IRConstant(0, "int")),
                    then_body=[IRReturn(value=IRName("x"))],
                    else_body=[IRReturn(value=IRConstant(0, "int"))],
                )
            ],
        )
        prog = IRProgram(functions=[func])
        js_code = self.generator.generate(prog)

        self.assertIn("if (x > 0) {", js_code)
        self.assertIn("return x;", js_code)
        self.assertIn("} else {", js_code)
        self.assertIn("return 0;", js_code)

    def test_while_loop_syntax_structural(self):
        """Verify while loop generation produces valid JavaScript syntax."""
        func = IRFunction(
            name="countDown",
            parameters=["n"],
            body=[
                IRAssignment("i", IRName("n")),
                IRWhile(
                    condition=IRBinaryOperation(left=IRName("i"), operator=">", right=IRConstant(0, "int")),
                    body=[
                        IRAssignment("i", IRBinaryOperation(left=IRName("i"), operator="-", right=IRConstant(1, "int")))
                    ],
                ),
                IRReturn(value=IRName("i")),
            ],
        )
        prog = IRProgram(functions=[func])
        js_code = self.generator.generate(prog)

        self.assertIn("let i = n;", js_code)
        self.assertIn("while (i > 0) {", js_code)
        self.assertIn("i = i - 1;", js_code)

    def test_print_mapping_structural(self):
        """Verify print mapping produces console.log without extra wrappers."""
        stmt = IRExpressionStatement(
            expression=IRFunctionCall(name="print", arguments=[IRConstant("Hello Rosetta", "str")])
        )
        prog = IRProgram(statements=[stmt])
        js_code = self.generator.generate(prog)

        self.assertEqual(js_code, 'console.log("Hello Rosetta");')

    def test_collections_syntax_structural(self):
        """Verify collections produce native arrays and objects."""
        prog = IRProgram(
            statements=[
                IRAssignment("items", IRList([IRConstant("apple", "str"), IRConstant("banana", "str")])),
                IRAssignment("prices", IRDict([IRConstant("apple", "str")], [IRConstant(1.5, "float")])),
            ]
        )
        js_code = self.generator.generate(prog)

        self.assertIn('let items = ["apple", "banana"];', js_code)
        self.assertIn('let prices = {"apple": 1.5};', js_code)

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_add_function_output_30(self):
        """Live Node.js test: add(10, 20) prints 30."""
        code = """def add(a: int, b: int) -> int:
    return a + b

print(add(10, 20))
"""
        ir_prog = build_ir(code)
        js_source = self.engine.translate(ir_prog, "javascript")

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        self.assertEqual(result.stdout.strip(), "30")

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_countdown_while_loop_output(self):
        """Live Node.js test: countdown(3) prints 3, 2, 1."""
        code = """def countdown(n: int) -> None:
    count = n
    while count > 0:
        print(count)
        count = count - 1

countdown(3)
"""
        ir_prog = build_ir(code)
        js_source = self.engine.translate(ir_prog, "javascript")

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        self.assertEqual(lines, ["3", "2", "1"])

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_if_else_execution(self):
        """Live Node.js test: if/else branch execution."""
        code = """def check(x: int) -> int:
    if x > 10:
        return x * 2
    else:
        return x + 1

print(check(15))
print(check(5))
"""
        ir_prog = build_ir(code)
        js_source = self.engine.translate(ir_prog, "javascript")

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        self.assertEqual(lines, ["30", "6"])

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_for_range_loop_execution(self):
        """Live Node.js test: for i in range(5) loop accumulating sum."""
        code = """def compute_sum() -> int:
    total = 0
    for i in range(5):
        total = total + i
    return total

print(compute_sum())
"""
        ir_prog = build_ir(code)
        js_source = self.engine.translate(ir_prog, "javascript")

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        self.assertEqual(result.stdout.strip(), "10")

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_for_of_array_iteration(self):
        """Live Node.js test: for ... of iterable collection."""
        prog = IRProgram(
            statements=[
                IRAssignment("items", IRList([IRConstant(10, "int"), IRConstant(20, "int"), IRConstant(30, "int")])),
                IRFor(
                    variable="item",
                    iterable=IRName("items"),
                    body=[IRExpressionStatement(IRFunctionCall("print", [IRName("item")]))],
                ),
            ]
        )
        js_source = self.generator.generate(prog)

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        self.assertEqual(lines, ["10", "20", "30"])

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_variable_reassignment(self):
        """Live Node.js test: variable scoping and reassignment."""
        code = """x = 5
x = x * 2
x = x + 3
print(x)
"""
        ir_prog = build_ir(code)
        js_source = self.engine.translate(ir_prog, "javascript")

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        self.assertEqual(result.stdout.strip(), "13")

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_strict_equality_execution(self):
        """Live Node.js test: strict equality behavior."""
        code = """def test_equality(a: int, b: int) -> str:
    if a == b:
        return "EQUAL"
    else:
        return "NOT_EQUAL"

print(test_equality(5, 5))
print(test_equality(5, 6))
"""
        ir_prog = build_ir(code)
        js_source = self.engine.translate(ir_prog, "javascript")

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        self.assertEqual(lines, ["EQUAL", "NOT_EQUAL"])

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_array_and_object_evaluation(self):
        """Live Node.js test: arrays and objects with length property."""
        prog = IRProgram(
            statements=[
                IRAssignment("users", IRList([IRConstant("Alice", "str"), IRConstant("Bob", "str")])),
                IRAssignment("info", IRDict([IRConstant("city", "str")], [IRConstant("Wonderland", "str")])),
                IRExpressionStatement(IRFunctionCall("print", [IRFunctionCall("len", [IRName("users")])])),
            ]
        )
        js_source = self.generator.generate(prog)

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        self.assertEqual(result.stdout.strip(), "2")

    @unittest.skipIf(not NODE_AVAILABLE, "Node.js not found in local environment. Skipping live runtime tests.")
    def test_live_node_builtins_and_subscripts(self):
        """Live Node.js test: abs, min, max, str, indexing and slicing."""
        code = """nums = [10, 20, 30]
first = nums[0]
sub = nums[1:3]
print(first)
print(len(sub))
print(abs(-15))
print(min(10, 20))
print(max(10, 20))
print(str(100))
"""
        ir_prog = build_ir(code)
        js_source = self.engine.translate(ir_prog, "javascript")

        result = run_node_exec(js_source)
        self.assertEqual(
            result.returncode,
            0,
            f"Node.js execution failed with error:\n{result.stderr}\n\nGenerated JS:\n{js_source}",
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        self.assertEqual(lines, ["10", "2", "15", "10", "20", "100"])


if __name__ == "__main__":
    unittest.main()
