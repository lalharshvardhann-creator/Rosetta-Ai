import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.translation import TranslationEngine


def is_tool_available(tool_name: str) -> bool:
    import shutil
    return shutil.which(tool_name) is not None


class TestLivePhase13Validation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = TranslationEngine(register_defaults=True)
        cls.has_gxx = is_tool_available("g++")
        cls.has_node = is_tool_available("node")

    def run_cpp_code(self, cpp_code: str) -> str:
        if not self.has_gxx:
            self.skipTest("g++ not available on system")
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "prog.cpp")
            exe_file = os.path.join(tmpdir, "prog.exe")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(cpp_code)

            compile_res = subprocess.run(
                ["g++", "-std=c++14", src_file, "-o", exe_file],
                capture_output=True,
                text=True
            )
            self.assertEqual(compile_res.returncode, 0, f"C++ Compilation failed:\n{compile_res.stderr}\nCode:\n{cpp_code}")

            run_res = subprocess.run([exe_file], capture_output=True, text=True)
            self.assertEqual(run_res.returncode, 0, f"C++ Execution failed:\n{run_res.stderr}")
            return run_res.stdout.strip()

    def run_js_code(self, js_code: str) -> str:
        if not self.has_node:
            self.skipTest("node not available on system")
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "prog.js")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(js_code)

            run_res = subprocess.run(["node", src_file], capture_output=True, text=True)
            self.assertEqual(run_res.returncode, 0, f"Node.js execution failed:\n{run_res.stderr}\nCode:\n{js_code}")
            return run_res.stdout.strip()

    def test_live_break_continue_and_loop_else(self):
        py_src = """
def test_loops():
    found = 0
    for x in [1, 2, 3, 4, 5]:
        if x == 3:
            continue
        if x == 4:
            found = 4
            break
    else:
        found = 99
    print(found)

test_loops()
"""
        ir = build_ir(py_src)
        cpp_code = self.engine.translate(ir, "cpp")
        js_code = self.engine.translate(ir, "javascript")

        if self.has_gxx:
            cpp_out = self.run_cpp_code(cpp_code)
            self.assertEqual(cpp_out, "4")

        if self.has_node:
            js_out = self.run_js_code(js_code)
            self.assertEqual(js_out, "4")

    def test_live_chained_comparisons_and_lambdas(self):
        py_src = """
def test_features():
    val = 5
    is_mid = (1 < val < 10)
    sq = lambda x: x * x
    res = sq(val)
    if is_mid:
        print(res)
    else:
        print(0)

test_features()
"""
        ir = build_ir(py_src)
        cpp_code = self.engine.translate(ir, "cpp")
        js_code = self.engine.translate(ir, "javascript")

        if self.has_gxx:
            cpp_out = self.run_cpp_code(cpp_code)
            self.assertEqual(cpp_out, "25")

        if self.has_node:
            js_out = self.run_js_code(js_code)
            self.assertEqual(js_out, "25")

    def test_live_iterators_and_aggregations(self):
        py_src = """
def test_iterators():
    nums = [10, 20, 30]
    total = sum(nums)
    print(total)

test_iterators()
"""
        ir = build_ir(py_src)
        cpp_code = self.engine.translate(ir, "cpp")
        js_code = self.engine.translate(ir, "javascript")

        if self.has_gxx:
            cpp_out = self.run_cpp_code(cpp_code)
            self.assertEqual(cpp_out, "60")

        if self.has_node:
            js_out = self.run_js_code(js_code)
            self.assertEqual(js_out, "60")

    def test_live_comprehensions(self):
        py_src = """
def test_comps():
    squares = {x: x * x for x in range(4)}
    print(squares[3])

test_comps()
"""
        ir = build_ir(py_src)
        cpp_code = self.engine.translate(ir, "cpp")
        js_code = self.engine.translate(ir, "javascript")

        if self.has_gxx:
            cpp_out = self.run_cpp_code(cpp_code)
            self.assertEqual(cpp_out, "9")

        if self.has_node:
            js_out = self.run_js_code(js_code)
            self.assertEqual(js_out, "9")


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLivePhase13Validation)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
