"""
Rosetta AI - C++ Compilation & Syntax Validation Tests (Phase 7)
----------------------------------------------------------------
Tests live compilation using `g++` or `clang++` when available in the environment,
or cleanly skips live compilation tests with an explanatory notice if no C++ compiler is installed.
Includes static structural tests that validate generated C++ syntax on all platforms.
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
from app.translation import CppGenerator, TranslationEngine

GPP_PATH = shutil.which("g++")
CLANGPP_PATH = shutil.which("clang++")
CPP_COMPILER_PATH = GPP_PATH or CLANGPP_PATH
CPP_COMPILER_NAME = "g++" if GPP_PATH else ("clang++" if CLANGPP_PATH else None)
CPP_COMPILER_AVAILABLE = CPP_COMPILER_PATH is not None


def run_cpp_compile(cpp_source: str, std_version: str = "c++14") -> subprocess.CompletedProcess:
    """
    Helper function to compile a C++ source string using the detected compiler.
    Returns the CompletedProcess result (returncode, stdout, stderr).
    """
    if not CPP_COMPILER_AVAILABLE:
        raise RuntimeError("No C++ compiler (g++ or clang++) is available in this environment.")

    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / "program.cpp"
        exe_path = Path(tmpdir) / "program.exe"
        src_path.write_text(cpp_source, encoding="utf-8")

        cmd = [
            CPP_COMPILER_PATH,
            f"-std={std_version}",
            str(src_path),
            "-o",
            str(exe_path),
        ]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )


class TestCppCompilation(unittest.TestCase):
    """
    Compilation tests validating generated C++ code against real C++ compilers
    (g++ or clang++) when installed on the host machine.
    """

    def setUp(self):
        self.generator = CppGenerator()
        self.engine = TranslationEngine()

    def test_typed_arithmetic_generation(self):
        """Verify typed arithmetic generation produces valid C++ syntax."""
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
        cpp_code = self.generator.generate(program)

        self.assertIn("int add(int a, int b) {", cpp_code)
        self.assertIn("return a + b;", cpp_code)

    def test_typed_if_comparison_generation(self):
        """Verify typed if-else comparison generation produces valid C++ syntax."""
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
        cpp_code = self.generator.generate(program)

        self.assertIn("int checkPositive(int x) {", cpp_code)
        self.assertIn("if (x > 0) {", cpp_code)
        self.assertIn("return x;", cpp_code)
        self.assertIn("return 0;", cpp_code)

    def test_typed_while_loop_generation(self):
        """Verify typed while loop generation produces valid C++ syntax."""
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
        cpp_code = self.generator.generate(program)

        self.assertIn("int countdown(int n) {", cpp_code)
        self.assertIn("int count = n;", cpp_code)
        self.assertIn("while (count > 0) {", cpp_code)
        self.assertIn("count = count - 1;", cpp_code)
        self.assertIn("return count;", cpp_code)

    def test_print_mapping_generation(self):
        """Verify print mapping with String parameter produces valid C++ syntax."""
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
        cpp_code = self.generator.generate(program)

        self.assertIn("#include <iostream>", cpp_code)
        self.assertIn("#include <string>", cpp_code)
        self.assertIn("void greet(std::string msg) {", cpp_code)
        self.assertIn("std::cout << msg << std::endl;", cpp_code)

    def test_local_variable_inference_structural(self):
        """Verify local variable inference generates correct C++ types."""
        prog = IRProgram(
            statements=[
                IRAssignment("a", IRConstant(10, "int")),
                IRAssignment("b", IRConstant(20, "int")),
                IRAssignment("c", IRBinaryOperation(left=IRName("a"), operator="+", right=IRName("b"))),
            ]
        )
        cpp_code = self.generator.generate(prog)

        self.assertIn("int a = 10;", cpp_code)
        self.assertIn("int b = 20;", cpp_code)
        self.assertIn("int c = a + b;", cpp_code)

    def test_collection_vector_map_structural(self):
        """Verify collections generate std::vector and std::map with automatic includes."""
        prog = IRProgram(
            statements=[
                IRAssignment("items", IRList([IRConstant("apple", "str"), IRConstant("banana", "str")])),
                IRAssignment("prices", IRDict([IRConstant("apple", "str")], [IRConstant(1.5, "float")])),
            ]
        )
        cpp_code = self.generator.generate(prog)

        self.assertIn("#include <map>", cpp_code)
        self.assertIn("#include <string>", cpp_code)
        self.assertIn("#include <vector>", cpp_code)
        self.assertIn('std::vector<std::string> items = std::vector<std::string>{"apple", "banana"};', cpp_code)
        self.assertIn('std::map<std::string, double> prices = std::map<std::string, double>{{"apple", 1.5}};', cpp_code)

    def test_for_range_loop_structural(self):
        """Verify for-range loop generation produces valid C++ loop syntax."""
        prog = IRProgram(
            statements=[
                IRFor(
                    variable="i",
                    iterable=IRFunctionCall("range", [IRConstant(5, "int")]),
                    body=[
                        IRExpressionStatement(IRFunctionCall("print", [IRName("i")]))
                    ],
                )
            ]
        )
        cpp_code = self.generator.generate(prog)

        self.assertIn("for (int i = 0; i < 5; ++i) {", cpp_code)
        self.assertIn("std::cout << i << std::endl;", cpp_code)

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_add_function(self):
        """Live compilation test: def add(a: int, b: int) -> int: return a + b"""
        code = """def add(a: int, b: int) -> int:
    return a + b

print(add(2, 3))
"""
        ir_prog = build_ir(code)
        cpp_source = self.engine.translate(ir_prog, "cpp")

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_if_else(self):
        """Live compilation test: if/else with comparisons."""
        code = """def maximum(a: int, b: int) -> int:
    if a > b:
        return a
    else:
        return b

print(maximum(10, 20))
"""
        ir_prog = build_ir(code)
        cpp_source = self.engine.translate(ir_prog, "cpp")

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_while_loop(self):
        """Live compilation test: while loop arithmetic."""
        code = """def compute_sum(n: int) -> int:
    total: int = 0
    i: int = 1
    while i <= n:
        total = total + i
        i = i + 1
    return total

print(compute_sum(5))
"""
        ir_prog = build_ir(code)
        cpp_source = self.engine.translate(ir_prog, "cpp")

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_print_mapping(self):
        """Live compilation test: print mapping with std::cout."""
        code = """def log_message(msg: str) -> None:
    print(msg)

log_message("Hello from Rosetta AI C++")
"""
        ir_prog = build_ir(code)
        cpp_source = self.engine.translate(ir_prog, "cpp")

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_local_variable_inference(self):
        """Live compilation test: local variable type inference."""
        code = """def calculate_area(length: int, width: int) -> int:
    area = length * width
    return area

print(calculate_area(4, 5))
"""
        ir_prog = build_ir(code)
        cpp_source = self.engine.translate(ir_prog, "cpp")

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_collections(self):
        """Live compilation test: std::vector and std::map collections."""
        prog = IRProgram(
            statements=[
                IRAssignment("names", IRList([IRConstant("Alice", "str"), IRConstant("Bob", "str")])),
                IRAssignment("scores", IRDict([IRConstant("Alice", "str")], [IRConstant(95, "int")])),
                IRExpressionStatement(IRFunctionCall("print", [IRConstant("Collections compiled!", "str")])),
            ]
        )
        cpp_source = self.generator.generate(prog)

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_for_range_loop(self):
        """Live compilation test: for i in range(10) loop."""
        code = """def loop_print(n: int) -> None:
    for i in range(n):
        print(i)

loop_print(3)
"""
        ir_prog = build_ir(code)
        cpp_source = self.engine.translate(ir_prog, "cpp")

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )

    @unittest.skipIf(not CPP_COMPILER_AVAILABLE, "C++ compiler (g++/clang++) not found in local environment.")
    def test_live_compile_builtins_and_subscripts(self):
        """Live compilation test: abs, min, max, str, vector indexing."""
        code = """def test_helpers(a: int, b: int) -> None:
    items = [a, b, abs(a), min(a, b), max(a, b)]
    first = items[0]
    msg = str(first)
    print(msg)

test_helpers(-5, 10)
"""
        ir_prog = build_ir(code)
        cpp_source = self.engine.translate(ir_prog, "cpp")

        result = run_cpp_compile(cpp_source)
        self.assertEqual(
            result.returncode,
            0,
            f"C++ compilation failed with error:\n{result.stderr}\n\nGenerated C++:\n{cpp_source}",
        )


if __name__ == "__main__":
    unittest.main()
