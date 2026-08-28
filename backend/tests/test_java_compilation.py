"""
Unit and Integration Tests for Java Compilation & Syntax Validation (Phases 6.1 & 6.2).
Tests live compilation using `javac` when available in the environment,
or cleanly skips with an explanatory notice if JDK is not installed.
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
from app.translation import JavaGenerator, TranslationEngine

JAVAC_PATH = shutil.which("javac")
JAVAC_AVAILABLE = JAVAC_PATH is not None


def run_javac_compile(java_source: str, class_name: str = "Main") -> subprocess.CompletedProcess:
    """
    Helper function to compile a Java source code string using javac.
    Returns the CompletedProcess result (returncode, stdout, stderr).
    """
    if not JAVAC_AVAILABLE:
        raise RuntimeError("javac is not available in this environment.")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / f"{class_name}.java"
        file_path.write_text(java_source, encoding="utf-8")
        return subprocess.run(
            [JAVAC_PATH, str(file_path)],
            capture_output=True,
            text=True,
            timeout=15,
        )


class TestJavaCompilation(unittest.TestCase):
    """
    Compilation tests that validate generated Java against the actual javac compiler
    when JDK is installed on the host machine.
    """

    def setUp(self):
        self.generator = JavaGenerator()
        self.engine = TranslationEngine()

    def test_typed_arithmetic_generation(self):
        """Verify typed arithmetic generation produces compilable Java syntax."""
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
        program = IRProgram(functions=[func])
        java_code = self.generator.generate(program)

        self.assertIn("public static int add(int a, int b) {", java_code)
        self.assertIn("return a + b;", java_code)

    def test_typed_if_comparison_generation(self):
        """Verify typed if-else comparison generation produces compilable Java syntax."""
        func = IRFunction(
            name="checkPositive",
            parameters=["x"],
            parameter_types={"x": "int"},
            return_type="int",
            body=[
                IRIf(
                    condition=IRBinaryOperation(left=IRName("x"), operator=">", right=IRConstant(0, "int")),
                    then_body=[IRReturn(value=IRName("x"))],
                    else_body=[IRReturn(value=IRConstant(0, "int"))],
                )
            ],
        )
        program = IRProgram(functions=[func])
        java_code = self.generator.generate(program)

        self.assertIn("public static int checkPositive(int x) {", java_code)
        self.assertIn("if (x > 0) {", java_code)
        self.assertIn("return x;", java_code)
        self.assertIn("return 0;", java_code)

    def test_typed_while_loop_generation(self):
        """Verify typed while loop generation produces compilable Java syntax."""
        func = IRFunction(
            name="countdown",
            parameters=["n"],
            parameter_types={"n": "int"},
            return_type="int",
            body=[
                IRAssignment(target="count", value=IRName("n"), var_type="int"),
                IRWhile(
                    condition=IRBinaryOperation(left=IRName("count"), operator=">", right=IRConstant(0, "int")),
                    body=[
                        IRAssignment(
                            target="count",
                            value=IRBinaryOperation(left=IRName("count"), operator="-", right=IRConstant(1, "int")),
                        )
                    ],
                ),
                IRReturn(value=IRName("count")),
            ],
        )
        program = IRProgram(functions=[func])
        java_code = self.generator.generate(program)

        self.assertIn("public static int countdown(int n) {", java_code)
        self.assertIn("int count = n;", java_code)
        self.assertIn("while (count > 0) {", java_code)
        self.assertIn("count = count - 1;", java_code)
        self.assertIn("return count;", java_code)

    def test_print_mapping_generation(self):
        """Verify print mapping with String parameter produces compilable Java syntax."""
        func = IRFunction(
            name="greet",
            parameters=["msg"],
            parameter_types={"msg": "str"},
            return_type="void",
            body=[
                IRExpressionStatement(
                    expression=IRFunctionCall(name="print", arguments=[IRName("msg")])
                )
            ],
        )
        program = IRProgram(functions=[func])
        java_code = self.generator.generate(program)

        self.assertIn("public static void greet(String msg) {", java_code)
        self.assertIn("System.out.println(msg);", java_code)

    def test_local_variable_inference_structural(self):
        """Verify local variable inference generates correct Java types."""
        prog = IRProgram(
            statements=[
                IRAssignment("a", IRConstant(10, "int")),
                IRAssignment("b", IRConstant(20, "int")),
                IRAssignment("c", IRBinaryOperation(left=IRName("a"), operator="+", right=IRName("b"))),
            ]
        )
        java_code = self.generator.generate(prog)

        self.assertIn("int a = 10;", java_code)
        self.assertIn("int b = 20;", java_code)
        self.assertIn("int c = a + b;", java_code)

    def test_collection_list_map_structural(self):
        """Verify collections generate List and Map with automatic import headers."""
        prog = IRProgram(
            statements=[
                IRAssignment("items", IRList([IRConstant("apple", "str"), IRConstant("banana", "str")])),
                IRAssignment("prices", IRDict([IRConstant("apple", "str")], [IRConstant(1.5, "float")])),
            ]
        )
        java_code = self.generator.generate(prog)

        self.assertIn("import java.util.Arrays;", java_code)
        self.assertIn("import java.util.HashMap;", java_code)
        self.assertIn("import java.util.List;", java_code)
        self.assertIn("import java.util.Map;", java_code)
        self.assertIn('List<Object> items = Arrays.asList("apple", "banana");', java_code)
        self.assertIn('Map<Object, Object> prices = Map.of("apple", 1.5);', java_code)

    @unittest.skipIf(not JAVAC_AVAILABLE, "JDK (javac) not found in local environment. Skipping live compilation.")
    def test_live_javac_compile_add_function(self):
        """Live compilation test: def add(a: int, b: int) -> int: return a + b"""
        code = """def add(a: int, b: int) -> int:
    return a + b
"""
        ir_prog = build_ir(code)
        java_source = self.engine.translate(ir_prog, "java")

        result = run_javac_compile(java_source, class_name="Main")
        self.assertEqual(
            result.returncode,
            0,
            f"javac compilation failed with error:\n{result.stderr}\n\nGenerated Java:\n{java_source}",
        )

    @unittest.skipIf(not JAVAC_AVAILABLE, "JDK (javac) not found in local environment. Skipping live compilation.")
    def test_live_javac_compile_if_else(self):
        """Live compilation test: if/else with comparisons."""
        code = """def maximum(a: int, b: int) -> int:
    if a > b:
        return a
    else:
        return b
"""
        ir_prog = build_ir(code)
        java_source = self.engine.translate(ir_prog, "java")

        result = run_javac_compile(java_source, class_name="Main")
        self.assertEqual(
            result.returncode,
            0,
            f"javac compilation failed with error:\n{result.stderr}\n\nGenerated Java:\n{java_source}",
        )

    @unittest.skipIf(not JAVAC_AVAILABLE, "JDK (javac) not found in local environment. Skipping live compilation.")
    def test_live_javac_compile_while_loop(self):
        """Live compilation test: while loop arithmetic."""
        code = """def compute_sum(n: int) -> int:
    total: int = 0
    i: int = 1
    while i <= n:
        total = total + i
        i = i + 1
    return total
"""
        ir_prog = build_ir(code)
        java_source = self.engine.translate(ir_prog, "java")

        result = run_javac_compile(java_source, class_name="Main")
        self.assertEqual(
            result.returncode,
            0,
            f"javac compilation failed with error:\n{result.stderr}\n\nGenerated Java:\n{java_source}",
        )

    @unittest.skipIf(not JAVAC_AVAILABLE, "JDK (javac) not found in local environment. Skipping live compilation.")
    def test_live_javac_compile_print_mapping(self):
        """Live compilation test: System.out.println mapping."""
        code = """def log_message(msg: str) -> None:
    print(msg)
"""
        ir_prog = build_ir(code)
        java_source = self.engine.translate(ir_prog, "java")

        result = run_javac_compile(java_source, class_name="Main")
        self.assertEqual(
            result.returncode,
            0,
            f"javac compilation failed with error:\n{result.stderr}\n\nGenerated Java:\n{java_source}",
        )

    @unittest.skipIf(not JAVAC_AVAILABLE, "JDK (javac) not found in local environment. Skipping live compilation.")
    def test_live_javac_compile_local_variable_inference(self):
        """Live compilation test: local variable inference."""
        code = """def calculate_area(length: int, width: int) -> int:
    area = length * width
    return area
"""
        ir_prog = build_ir(code)
        java_source = self.engine.translate(ir_prog, "java")

        result = run_javac_compile(java_source, class_name="Main")
        self.assertEqual(
            result.returncode,
            0,
            f"javac compilation failed with error:\n{result.stderr}\n\nGenerated Java:\n{java_source}",
        )

    @unittest.skipIf(not JAVAC_AVAILABLE, "JDK (javac) not found in local environment. Skipping live compilation.")
    def test_live_javac_compile_collections(self):
        """Live compilation test: List and Map collections."""
        prog = IRProgram(
            statements=[
                IRAssignment("names", IRList([IRConstant("Alice", "str"), IRConstant("Bob", "str")]))
            ]
        )
        java_source = self.generator.generate(prog)

        result = run_javac_compile(java_source, class_name="Main")
        self.assertEqual(
            result.returncode,
            0,
            f"javac compilation failed with error:\n{result.stderr}\n\nGenerated Java:\n{java_source}",
        )


if __name__ == "__main__":
    unittest.main()
