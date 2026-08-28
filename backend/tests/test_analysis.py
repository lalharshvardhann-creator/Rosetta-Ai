"""
Rosetta AI - Unit & Integration Tests for Code Analysis (Phase: Analysis)
-------------------------------------------------------------------------
Tests Pseudocode Generation, Time Complexity estimation, Space Complexity estimation,
and the /api/analyze REST API endpoint.
"""

import sys
from pathlib import Path
import unittest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.analyzer import (
    analyze_code,
    analyze_complexity,
    generate_pseudocode,
    ComplexityAnalyzer,
    PseudocodeGenerator,
)
from app.main import app


class TestCodeAnalysis(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_pseudocode_simple_function(self):
        """Test pseudocode generation for basic function."""
        code = "def add(a, b):\n    return a + b"
        result = generate_pseudocode(code)
        self.assertIn("START", result)
        self.assertIn("FUNCTION add(a, b)", result)
        self.assertIn("RETURN a + b", result)
        self.assertIn("END FUNCTION", result)
        self.assertIn("END", result)

    def test_pseudocode_for_range(self):
        """Test pseudocode generation for range loop (0 to 4)."""
        code = "for i in range(5):\n    print(i)"
        result = generate_pseudocode(code)
        self.assertIn("START", result)
        self.assertIn("FOR i FROM 0 TO 4", result)
        self.assertIn("PRINT i", result)
        self.assertIn("END FOR", result)
        self.assertIn("END", result)

    def test_pseudocode_if_else_and_while(self):
        """Test pseudocode for conditionals and while loop."""
        code = (
            "count = 0\n"
            "while count < 10:\n"
            "    if count % 2 == 0:\n"
            "        print(count)\n"
            "    else:\n"
            "        pass\n"
            "    count += 1"
        )
        result = generate_pseudocode(code)
        self.assertIn("WHILE count < 10 DO", result)
        self.assertIn("IF count % 2 == 0 THEN", result)
        self.assertIn("PRINT count", result)
        self.assertIn("ELSE", result)
        self.assertIn("END IF", result)
        self.assertIn("END WHILE", result)

    def test_pseudocode_empty_source(self):
        """Test pseudocode for empty or whitespace source."""
        self.assertEqual(generate_pseudocode(""), "START\nEND")
        self.assertEqual(generate_pseudocode("   \n  "), "START\nEND")

    def test_simple_o1_code(self):
        """Test simple O(1) constant time & space statements and functions."""
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(1)")
        self.assertEqual(res.space_complexity, "O(1)")
        self.assertTrue(len(res.time_explanation) > 0)
        self.assertTrue(len(res.space_explanation) > 0)

    def test_single_on_loop(self):
        """Test single O(n) loop over range/collection."""
        code = "def print_items(n):\n    for i in range(n):\n        print(i)"
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(n)")
        self.assertEqual(res.space_complexity, "O(1)")

    def test_nested_on2_loops(self):
        """Test nested O(n^2) loops."""
        code = (
            "def matrix_print(n):\n"
            "    for i in range(n):\n"
            "        for j in range(n):\n"
            "            print(i, j)"
        )
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(n^2)")
        self.assertEqual(res.space_complexity, "O(1)")

    def test_sequential_loops(self):
        """Test sequential O(n) loops simplifying to O(n)."""
        code = (
            "def process(items):\n"
            "    for x in items:\n"
            "        print(x)\n"
            "    for y in items:\n"
            "        print(y * 2)"
        )
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(n)")
        self.assertEqual(res.space_complexity, "O(1)")
        self.assertIn("sequential loops", res.time_explanation)

    def test_binary_search_while_loop(self):
        """Test binary search halving while loop pattern O(log n)."""
        code = (
            "def binary_search(arr, target):\n"
            "    low = 0\n"
            "    high = len(arr) - 1\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1"
        )
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(log n)")
        self.assertEqual(res.space_complexity, "O(1)")

    def test_list_creation_on_space(self):
        """Test list creation with list comprehension consuming O(n) space."""
        code = "def get_squares(n):\n    return [x * x for x in range(n)]"
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(n)")
        self.assertEqual(res.space_complexity, "O(n)")

    def test_array_multiplication_on_space(self):
        """Test array allocation [0] * n consuming O(n) space."""
        code = "def allocate_buffer(n):\n    arr = [0] * n\n    return arr"
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(n)")
        self.assertEqual(res.space_complexity, "O(n)")

    def test_constant_space_iterative_code(self):
        """Test iterative code with constant scalar variables O(1) space."""
        code = (
            "def compute_sum(nums):\n"
            "    total = 0\n"
            "    for x in nums:\n"
            "        total += x\n"
            "    return total"
        )
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(n)")
        self.assertEqual(res.space_complexity, "O(1)")

    def test_simple_linear_recursion(self):
        """Test linear recursion factorial O(n) time and O(n) stack space."""
        code = (
            "def factorial(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)"
        )
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(n)")
        self.assertEqual(res.space_complexity, "O(n)")

    def test_binary_search_recursion(self):
        """Test divide-and-conquer recursion O(log n) time and O(log n) space."""
        code = (
            "def bs_rec(arr, target, l, r):\n"
            "    if l > r:\n"
            "        return -1\n"
            "    mid = (l + r) // 2\n"
            "    if arr[mid] == target:\n"
            "        return mid\n"
            "    if arr[mid] > target:\n"
            "        return bs_rec(arr, target, l, mid - 1)\n"
            "    return bs_rec(arr, target, mid + 1, r)"
        )
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(log n)")
        self.assertEqual(res.space_complexity, "O(log n)")

    def test_exponential_recursion(self):
        """Test exponential branching recursion (naive Fibonacci) O(2^n)."""
        code = (
            "def fib(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    return fib(n - 1) + fib(n - 2)"
        )
        res = analyze_complexity(code)
        self.assertEqual(res.time_complexity, "O(2^n)")
        self.assertEqual(res.space_complexity, "O(n)")

    def test_invalid_syntax_handling(self):
        """Test that invalid Python syntax raises ValueError cleanly."""
        code = "def broken(:"
        with self.assertRaises(ValueError):
            analyze_complexity(code)

    def test_empty_source_complexity(self):
        """Test empty source code returns O(1) time and space."""
        res = analyze_complexity("")
        self.assertEqual(res.time_complexity, "O(1)")
        self.assertEqual(res.space_complexity, "O(1)")

    def test_api_analyze_success_with_source(self):
        """Test POST /api/analyze with valid 'source' payload."""
        payload = {
            "source": "def add(a, b):\n    return a + b"
        }
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("FUNCTION add(a, b)", data.get("pseudocode", ""))
        self.assertEqual(data.get("time_complexity"), "O(1)")
        self.assertEqual(data.get("space_complexity"), "O(1)")
        self.assertIsNotNone(data.get("time_explanation"))
        self.assertIsNotNone(data.get("space_explanation"))

    def test_api_analyze_success_with_source_code_alias(self):
        """Test POST /api/analyze with 'source_code' alias payload."""
        payload = {
            "source_code": "for i in range(5):\n    print(i)"
        }
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("FOR i FROM 0 TO 4", data.get("pseudocode", ""))

    def test_api_analyze_empty_source_400(self):
        """Test POST /api/analyze with empty source returns 400."""
        response = self.client.post("/api/analyze", json={"source": ""})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("source must not be empty", data.get("error", ""))

    def test_api_analyze_syntax_error_400(self):
        """Test POST /api/analyze with invalid Python syntax returns 400."""
        payload = {"source": "def func(:\n    pass"}
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("syntax", data.get("error", "").lower())


if __name__ == "__main__":
    unittest.main()
