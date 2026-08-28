"""
Rosetta AI - Cross-Target Consistency Test Suite (Phase 10)
------------------------------------------------------------
Validates that the SAME Python programs translate consistently across all 3
target language generators (Java, C++, JavaScript) with equivalent semantics:
1. Arithmetic expressions & operator precedence
2. Conditional branching (if / else)
3. While loop execution
4. For range loop iteration
5. List and nested list generation
6. Dict and nested dict generation
7. Subscript indexing & slicing
8. Built-in mathematical functions (abs, min, max)
9. Built-in type casting functions (str, int, float, bool)
10. Built-in inspection & I/O (len, print)
11. Multi-parameter functions
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.translation import TranslationEngine


class TestCrossTargetConsistency(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine(register_defaults=True)

    def translate_all(self, python_code: str):
        """Helper to build IR and translate to Java, C++, and JavaScript."""
        ir = build_ir(python_code)
        java_out = self.engine.translate(ir, "java")
        cpp_out = self.engine.translate(ir, "cpp")
        js_out = self.engine.translate(ir, "javascript")
        return java_out, cpp_out, js_out

    def test_1_arithmetic_expressions(self):
        """Test arithmetic expressions translated consistently across all targets."""
        src = """def calculate(a: int, b: int) -> int:
    return a + b * 2 - 5
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("public static int calculate(int a, int b)", java)
        self.assertIn("return a + b * 2 - 5;", java)

        self.assertIn("int calculate(int a, int b)", cpp)
        self.assertIn("return a + b * 2 - 5;", cpp)

        self.assertIn("function calculate(a, b)", js)
        self.assertIn("return a + b * 2 - 5;", js)

    def test_2_if_else_branching(self):
        """Test if / else branching across all targets."""
        src = """def check_sign(n: int) -> str:
    if n > 0:
        return "positive"
    else:
        return "non-positive"
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("if (n > 0)", java)
        self.assertIn('return "positive";', java)
        self.assertIn('return "non-positive";', java)

        self.assertIn("if (n > 0)", cpp)
        self.assertIn('return "positive";', cpp)
        self.assertIn('return "non-positive";', cpp)

        self.assertIn("if (n > 0)", js)
        self.assertIn('return "positive";', js)
        self.assertIn('return "non-positive";', js)

    def test_3_while_loop(self):
        """Test while loop across all targets."""
        src = """def countdown(start: int) -> int:
    count: int = start
    while count > 0:
        count = count - 1
    return count
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("while (count > 0)", java)
        self.assertIn("while (count > 0)", cpp)
        self.assertIn("while (count > 0)", js)

    def test_4_for_range_loop(self):
        """Test for range loop across all targets."""
        src = """def sum_range(n: int) -> int:
    total: int = 0
    for i in range(n):
        total = total + i
    return total
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("for (int i = 0; i < n; i++)", java)
        self.assertIn("for (int i = 0; i < n; ++i)", cpp)
        self.assertIn("for (let i = 0; i < n; i++)", js)

    def test_5_list_creation_and_subscript(self):
        """Test list creation and element access across all targets."""
        src = """def get_first() -> int:
    items = [10, 20, 30]
    return items[0]
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("Arrays.asList(10, 20, 30)", java)
        self.assertIn("items.get(0)", java)

        self.assertIn("std::vector<int>{10, 20, 30}", cpp)
        self.assertIn("items[0]", cpp)

        self.assertIn("[10, 20, 30]", js)
        self.assertIn("items[0]", js)

    def test_6_dict_creation(self):
        """Test dictionary creation across all targets."""
        src = """def make_dict():
    data = {"apple": 1, "banana": 2}
    return data
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn('Map.of("apple", 1, "banana", 2)', java)
        self.assertIn('std::map<std::string, int>{{"apple", 1}, {"banana", 2}}', cpp)
        self.assertIn('"apple": 1', js)
        self.assertIn('"banana": 2', js)

    def test_7_builtin_math_functions(self):
        """Test abs, min, and max built-in function mappings."""
        src = """def math_helpers(a: int, b: int) -> int:
    x: int = abs(a)
    y: int = min(a, b)
    z: int = max(a, b)
    return x + y + z
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("Math.abs(a)", java)
        self.assertIn("Math.min(a, b)", java)
        self.assertIn("Math.max(a, b)", java)

        self.assertIn("std::abs(a)", cpp)
        self.assertIn("std::min(a, b)", cpp)
        self.assertIn("std::max(a, b)", cpp)
        self.assertIn("#include <cmath>", cpp)
        self.assertIn("#include <algorithm>", cpp)

        self.assertIn("Math.abs(a)", js)
        self.assertIn("Math.min(a, b)", js)
        self.assertIn("Math.max(a, b)", js)

    def test_8_builtin_type_casting(self):
        """Test str, int, float, bool built-in type conversions."""
        src = """def cast_demo(num: int):
    s = str(num)
    i = int(num)
    f = float(num)
    b = bool(num)
    print(s, i, f, b)
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("String.valueOf(num)", java)
        self.assertIn("(int) (num)", java)
        self.assertIn("(double) (num)", java)
        self.assertIn("Boolean.parseBoolean(String.valueOf(num))", java)

        self.assertIn("std::to_string(num)", cpp)
        self.assertIn("static_cast<int>(num)", cpp)
        self.assertIn("static_cast<double>(num)", cpp)
        self.assertIn("static_cast<bool>(num)", cpp)

        self.assertIn("String(num)", js)
        self.assertIn("parseInt(num, 10)", js)
        self.assertIn("parseFloat(num)", js)
        self.assertIn("Boolean(num)", js)

    def test_9_builtin_len_and_print(self):
        """Test len and print built-ins across all targets."""
        src = """items = [1, 2, 3]
print(len(items))
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("System.out.println(items.size());", java)

        self.assertIn("std::cout << items.size() << std::endl;", cpp)

        self.assertIn("console.log(items.length);", js)

    def test_10_nested_expressions_and_collections(self):
        """Test nested expressions and nested collections."""
        src = """def nested_demo():
    matrix = [[1, 2], [3, 4]]
    return matrix[0]
"""
        java, cpp, js = self.translate_all(src)

        self.assertIn("Arrays.asList(Arrays.asList(1, 2), Arrays.asList(3, 4))", java)
        self.assertIn("matrix.get(0)", java)

        self.assertIn("matrix[0]", cpp)
        self.assertIn("matrix[0]", js)


if __name__ == "__main__":
    unittest.main()
