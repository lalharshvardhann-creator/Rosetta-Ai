"""
Unit tests for Rosetta AI Python AST Analyzer.
Uses Python's built-in `unittest` framework (zero external dependencies required).
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.analyzer.python_parser import analyze_python_code


class TestPythonASTAnalyzer(unittest.TestCase):

    def test_simple_function_add(self):
        """Test the canonical hackathon example: def add(a, b): return a + b"""
        code = """def add(a, b):
    return a + b
"""
        result = analyze_python_code(code)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["functions"]), 1)

        func = result["functions"][0]
        self.assertEqual(func["name"], "add")
        self.assertEqual(func["parameters"], ["a", "b"])
        self.assertEqual(func["returns"], ["a + b"])

        bin_ops = [
            expr for expr in result["expressions"]
            if expr["type"] == "binary_operation"
        ]
        self.assertTrue(len(bin_ops) >= 1)
        self.assertEqual(bin_ops[0]["operator"], "Add")
        self.assertEqual(bin_ops[0]["code"], "a + b")

    def test_class_and_methods(self):
        """Test parsing classes, inheritance, and methods."""
        code = """class Calculator(BaseCalc):
    def multiply(self, x, y):
        return x * y
"""
        result = analyze_python_code(code)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["classes"]), 1)

        cls = result["classes"][0]
        self.assertEqual(cls["name"], "Calculator")
        self.assertEqual(cls["bases"], ["BaseCalc"])
        self.assertIn("multiply", cls["methods"])

        self.assertEqual(len(result["functions"]), 1)
        self.assertEqual(result["functions"][0]["name"], "multiply")
        self.assertEqual(result["functions"][0]["parameters"], ["self", "x", "y"])

    def test_variables_and_constants(self):
        """Test variable assignments and constants."""
        code = """total = 100
name = "Rosetta"
is_active = True
"""
        result = analyze_python_code(code)

        self.assertTrue(result["success"])
        var_names = [v["name"] for v in result["variables"]]
        self.assertIn("total", var_names)
        self.assertIn("name", var_names)
        self.assertIn("is_active", var_names)

        const_vals = [c["value"] for c in result["constants"]]
        self.assertIn(100, const_vals)
        self.assertIn("Rosetta", const_vals)
        self.assertIn(True, const_vals)

    def test_control_flow(self):
        """Test if/else, for loops, and while loops."""
        code = """if x > 0:
    print(x)
else:
    print(-x)

for i in range(10):
    pass

while count < 5:
    count += 1
"""
        result = analyze_python_code(code)

        self.assertTrue(result["success"])
        flow_types = [cf["type"] for cf in result["control_flow"]]
        self.assertIn("if", flow_types)
        self.assertIn("for", flow_types)
        self.assertIn("while", flow_types)

    def test_imports(self):
        """Test standard imports and from-imports."""
        code = """import os
import math as m
from typing import List, Dict
"""
        result = analyze_python_code(code)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["imports"]), 3)

        modules = [imp["module"] for imp in result["imports"] if imp["type"] == "import_from"]
        self.assertIn("typing", modules)

    def test_syntax_error_handling(self):
        """Test that syntax errors are caught cleanly without crashing."""
        broken_code = "def broken_func(:"
        result = analyze_python_code(broken_code)

        self.assertFalse(result["success"])
        self.assertIn("SyntaxError", result["error"])
        self.assertEqual(result["line"], 1)


if __name__ == "__main__":
    unittest.main()
