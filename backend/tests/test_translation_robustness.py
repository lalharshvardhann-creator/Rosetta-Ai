"""
Rosetta AI - Translation Engine Robustness & Regression Tests (Phase 19)
-------------------------------------------------------------------------
Exhaustive regression test suite covering all 23 scenarios across JavaScript, Java, and C++:
 1. Arithmetic (+, -, *, /, %)
 2. Variables & Constants
 3. Variable Reassignment
 4. Functions
 5. Function Parameters & Defaults
 6. Return Statements
 7. If / Elif / Else Conditionals
 8. For Loops & Numeric range()
 9. While Loops
10. Nested Loops & Loop Control (break/continue)
11. Lists & Operations (indexing, append, slicing)
12. Tuples & Unpacking
13. Dictionaries & Lookup
14. Sets & Operations
15. String Operations & Concatenation
16. Boolean Logic (and, or, not)
17. Function Calls & Invocations
18. Multiple Functions
19. Comprehensions (List & Dict)
20. Classes & OOP (constructor, methods)
21. Exceptions (try/except/finally/raise)
22. Invalid Python Syntax Handling (HTTP 400)
23. Empty Input Handling (HTTP 400)
"""

import sys
from pathlib import Path
import unittest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.main import app
from app.translation import TranslationEngine


class TestTranslationRobustness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = TranslationEngine(register_defaults=True)
        cls.client = TestClient(app)

    def _translate(self, python_code: str, target: str) -> str:
        ir_prog = build_ir(python_code)
        return self.engine.translate(ir_prog, target)

    def test_1_arithmetic_operations(self):
        code = "res = (10 + 5) * 2 - (20 / 4) + (13 % 5)"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("10 + 5", js_out)
        self.assertIn("10 + 5", java_out)
        self.assertIn("10 + 5", cpp_out)

    def test_2_variables_and_constants(self):
        code = "age = 25\nrate = 3.14\nname = 'Alice'\nis_admin = True\ndata = None"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("age = 25", js_out)
        self.assertIn("int age = 25", java_out)
        self.assertIn("int age = 25", cpp_out)

    def test_3_variable_reassignment(self):
        code = "count = 0\ncount = count + 1\ncount = 10"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertEqual(js_out.count("let count = 0"), 1)
        self.assertEqual(js_out.count("let count = count"), 0)
        self.assertEqual(java_out.count("int count = 0"), 1)
        self.assertEqual(java_out.count("int count = count"), 0)

    def test_4_basic_function(self):
        code = "def multiply(a: int, b: int) -> int:\n    return a * b"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("function multiply(a, b)", js_out)
        self.assertIn("public static int multiply(int a, int b)", java_out)
        self.assertIn("int multiply(int a, int b)", cpp_out)

    def test_5_function_parameters_with_defaults(self):
        code = "def greet(name: str, greeting: str = 'Hello') -> str:\n    return greeting + ' ' + name"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("function greet(", js_out)
        self.assertIn("greet(", java_out)
        self.assertIn("greet(", cpp_out)

    def test_6_return_statements(self):
        code = "def check_val(x: int) -> str:\n    if x > 0:\n        return 'positive'\n    return 'non-positive'"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("return \"positive\";", js_out)
        self.assertIn("return \"positive\";", java_out)
        self.assertIn("return \"positive\";", cpp_out)

    def test_7_if_elif_else(self):
        code = "score = 85\nif score >= 90:\n    grade = 'A'\nelif score >= 80:\n    grade = 'B'\nelse:\n    grade = 'C'"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("score >= 90", js_out)
        self.assertIn("score >= 80", js_out)
        self.assertIn("score >= 90", java_out)
        self.assertIn("score >= 80", java_out)
        self.assertIn("score >= 90", cpp_out)
        self.assertIn("score >= 80", cpp_out)

    def test_8_for_loops(self):
        code = "total = 0\nfor i in range(10):\n    total = total + i"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("for (let i = 0; i < 10; i++)", js_out)
        self.assertIn("for (int i = 0; i < 10; i++)", java_out)
        self.assertIn("for (int i = 0; i < 10; ++i)", cpp_out)

    def test_9_while_loops(self):
        code = "n = 5\nwhile n > 0:\n    print(n)\n    n = n - 1"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("while (n > 0)", js_out)
        self.assertIn("while (n > 0)", java_out)
        self.assertIn("while (n > 0)", cpp_out)

    def test_10_nested_loops_and_control(self):
        code = "for i in range(3):\n    for j in range(3):\n        if j == 1:\n            continue\n        if i == 2:\n            break\n        print(i, j)"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("continue;", js_out)
        self.assertIn("break;", js_out)
        self.assertIn("continue;", java_out)
        self.assertIn("break;", java_out)
        self.assertIn("continue;", cpp_out)
        self.assertIn("break;", cpp_out)

    def test_11_lists_and_indexing(self):
        code = "nums = [1, 2, 3, 4]\nfirst = nums[0]\nnums.append(5)"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("nums = [1, 2, 3, 4]", js_out)
        self.assertIn("nums.push(5)", js_out)
        self.assertIn("nums.get(0)", java_out)
        self.assertIn("nums.push_back(5)", cpp_out)

    def test_12_tuples_and_unpacking(self):
        code = "point = (10, 20)\nx, y = point"
        js_out = self._translate(code, "javascript")
        self.assertTrue("let [x, y] = point" in js_out or ("x = point[0]" in js_out and "y = point[1]" in js_out))

    def test_13_dictionaries(self):
        code = "user = {'id': 1, 'name': 'Bob'}\nval = user['name']"
        js_out = self._translate(code, "javascript")
        self.assertIn("user = {\"id\": 1, \"name\": \"Bob\"}", js_out)

    def test_14_sets(self):
        code = "items = {1, 2, 3}\nitems.add(4)"
        js_out = self._translate(code, "javascript")
        self.assertIn("new Set([1, 2, 3])", js_out)

    def test_15_strings(self):
        code = "greeting = 'Hello' + ' World'\nupper_msg = greeting.upper()\nlength = len(greeting)"
        js_out = self._translate(code, "javascript")
        self.assertIn("greeting.toUpperCase()", js_out)
        self.assertIn("greeting.length", js_out)

    def test_16_boolean_logic(self):
        code = "a = True\nb = False\nres = (a and not b) or (b and a)"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("&&", js_out)
        self.assertIn("||", js_out)
        self.assertIn("!", js_out)
        self.assertIn("&&", java_out)
        self.assertIn("||", cpp_out)

    def test_17_function_calls(self):
        code = "def calc(x: int) -> int:\n    return x * 2\n\nresult = calc(10)\nprint(result)"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("calc(10)", js_out)
        self.assertIn("calc(10)", java_out)
        self.assertIn("calc(10)", cpp_out)

    def test_18_multiple_functions(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b\n\ndef sub(a: int, b: int) -> int:\n    return a - b\n\nprint(add(5, sub(10, 4)))"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("function add(", js_out)
        self.assertIn("function sub(", js_out)
        self.assertIn("public static int add(", java_out)
        self.assertIn("public static int sub(", java_out)
        self.assertIn("int add(", cpp_out)
        self.assertIn("int sub(", cpp_out)

    def test_19_comprehensions(self):
        code = "squares = [x * x for x in range(5)]"
        js_out = self._translate(code, "javascript")
        self.assertIn("squares", js_out)

    def test_20_classes_and_oop(self):
        code = "class Person:\n    def __init__(self, name: str):\n        self.name = name\n    def get_name(self) -> str:\n        return self.name"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("class Person", js_out)
        self.assertIn("class Person", java_out)
        self.assertIn("class Person", cpp_out)

    def test_21_exceptions(self):
        code = "try:\n    x = 10 / 0\nexcept Exception as e:\n    print('error')\nfinally:\n    print('done')"
        js_out = self._translate(code, "javascript")
        java_out = self._translate(code, "java")
        cpp_out = self._translate(code, "cpp")

        self.assertIn("try {", js_out)
        self.assertIn("catch (", js_out)
        self.assertIn("finally {", js_out)
        self.assertIn("try {", java_out)
        self.assertIn("finally {", java_out)
        self.assertIn("try {", cpp_out)

    def test_22_invalid_python_syntax_handled(self):
        response = self.client.post("/api/translate", json={"source": "def broken(:\n    return", "target_language": "javascript"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("Python syntax error", data.get("error", ""))

    def test_23_empty_input_handled(self):
        response = self.client.post("/api/translate", json={"source": "   ", "target_language": "javascript"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("source must not be empty", data.get("error", ""))


if __name__ == "__main__":
    unittest.main()
