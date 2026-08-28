"""
Unit tests for Python dictionaries, lists, and string advanced methods
across Java, C++, and JavaScript code generators.
"""

import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir import build_ir
from app.translation import TranslationEngine


class TestDictAndAdvancedCollections(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()

    def _translate(self, code: str):
        ir_prog = build_ir(code)
        java_out = self.engine.translate(ir_prog, "java")
        cpp_out = self.engine.translate(ir_prog, "cpp")
        js_out = self.engine.translate(ir_prog, "javascript")
        return java_out, cpp_out, js_out

    def test_dict_get_and_keys(self):
        code = """
data = {"a": 1, "b": 2}
val = data.get("a")
val_def = data.get("c", 0)
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn('data.get("a")', java_out)
        self.assertIn('data.getOrDefault("c", 0)', java_out)
        self.assertIn('data.count("a")', cpp_out)
        self.assertIn('data.hasOwnProperty("a")', js_out)

    def test_dict_items_iteration(self):
        code = """
data = {"x": 10, "y": 20}
for k, v in data.items():
    print(k)
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("data.entrySet()", java_out)
        self.assertIn("entry.getKey()", java_out)
        self.assertIn("entry.getValue()", java_out)
        self.assertIn("item_pair.first", cpp_out)
        self.assertIn("Object.entries(data)", js_out)

    def test_list_insert_and_index_and_reverse(self):
        code = """
nums = [1, 2, 3]
nums.insert(0, 99)
idx = nums.index(2)
nums.reverse()
nums.sort()
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn("nums.add(0, 99)", java_out)
        self.assertIn("nums.indexOf(2)", java_out)
        self.assertIn("Collections.reverse(nums)", java_out)
        self.assertIn("Collections.sort(nums)", java_out)

        self.assertIn("nums.insert(nums.begin() + (0), 99)", cpp_out)
        self.assertIn("std::reverse(nums.begin(), nums.end())", cpp_out)
        self.assertIn("std::sort(nums.begin(), nums.end())", cpp_out)

        self.assertIn("nums.splice(0, 0, 99)", js_out)
        self.assertIn("nums.indexOf(2)", js_out)
        self.assertIn("nums.reverse()", js_out)
        self.assertIn("nums.sort(", js_out)

    def test_string_methods(self):
        code = """
txt = "hello world"
a = txt.startswith("hello")
b = txt.endswith("world")
c = txt.replace("hello", "hi")
d = txt.find("world")
"""
        java_out, cpp_out, js_out = self._translate(code)

        self.assertIn('txt.startsWith("hello")', java_out)
        self.assertIn('txt.endsWith("world")', java_out)
        self.assertIn('txt.replace("hello", "hi")', java_out)
        self.assertIn('txt.indexOf("world")', java_out)

        self.assertIn('txt.rfind("hello", 0) == 0', cpp_out)
        self.assertIn('txt.find("world")', cpp_out)

        self.assertIn('txt.startsWith("hello")', js_out)
        self.assertIn('txt.endsWith("world")', js_out)
        self.assertIn('txt.replaceAll("hello", "hi")', js_out)
        self.assertIn('txt.indexOf("world")', js_out)


if __name__ == "__main__":
    unittest.main()
