"""
Rosetta AI - FastAPI End-to-End API Integration Tests (Phase 9)
---------------------------------------------------------------
Verifies REST API endpoints:
- GET /api/health check endpoint
- POST /api/translate for Java, C++, JavaScript (and aliases 'c++', 'cpp', 'js', 'javascript')
- Acceptance of both 'source' and 'source_code' request payload keys
- Input validation (empty source, missing source, empty language, unsupported language)
- Python syntax error handling (HTTP 400)
- Unsupported target language handling (HTTP 400)
- Translation error handling (HTTP 422)
- Response JSON schema validation (success, source_language, target_language, code, error)
- Structural verification of generated target code
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.translation.exceptions import UnsupportedIRNodeError, TranslationError


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_1_health_check_endpoint(self):
        """Test GET /api/health returns 200, status 'ok', and list of supported languages."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("engine"), "Rosetta AI")
        self.assertIn("java", data.get("supported_languages", []))
        self.assertIn("cpp", data.get("supported_languages", []))
        self.assertIn("javascript", data.get("supported_languages", []))

    def test_2_translate_to_java_success_with_source_key(self):
        """Test POST /api/translate with target_language='java' using 'source' key."""
        payload = {
            "source": "def add(a: int, b: int) -> int:\n    return a + b\n",
            "target_language": "java",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("source_language"), "python")
        self.assertEqual(data.get("target_language"), "java")
        self.assertIsNone(data.get("error"))
        self.assertIn("public class Main", data.get("code", ""))
        self.assertIn("public static int add(int a, int b)", data.get("code", ""))
        self.assertIn("return a + b;", data.get("code", ""))

    def test_3_translate_to_java_success_with_source_code_key(self):
        """Test POST /api/translate with target_language='java' using 'source_code' alias key."""
        payload = {
            "source_code": "def add(a: int, b: int) -> int:\n    return a + b\n",
            "target_language": "java",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("source_language"), "python")
        self.assertEqual(data.get("target_language"), "java")
        self.assertIn("public class Main", data.get("code", ""))

    def test_4_translate_to_cpp_success(self):
        """Test POST /api/translate with target_language='cpp'."""
        payload = {
            "source": "def add(a: int, b: int) -> int:\n    return a + b\n",
            "target_language": "cpp",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("source_language"), "python")
        self.assertEqual(data.get("target_language"), "cpp")
        self.assertIn("int add(int a, int b) {", data.get("code", ""))
        self.assertIn("return a + b;", data.get("code", ""))

    def test_5_translate_to_javascript_success(self):
        """Test POST /api/translate with target_language='javascript'."""
        payload = {
            "source": "def add(a: int, b: int) -> int:\n    return a + b\n",
            "target_language": "javascript",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("source_language"), "python")
        self.assertEqual(data.get("target_language"), "javascript")
        self.assertIn("function add(a, b) {", data.get("code", ""))
        self.assertIn("return a + b;", data.get("code", ""))

    def test_6_translate_cplusplus_alias(self):
        """Test POST /api/translate with alias 'c++' normalizes to 'cpp'."""
        payload = {
            "source": "def multiply(x: int, y: int) -> int:\n    return x * y\n",
            "target_language": "c++",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("target_language"), "cpp")
        self.assertIn("int multiply(int x, int y) {", data.get("code", ""))

    def test_7_translate_js_alias(self):
        """Test POST /api/translate with alias 'js' normalizes to 'javascript'."""
        payload = {
            "source": "def multiply(x: int, y: int) -> int:\n    return x * y\n",
            "target_language": "js",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("target_language"), "javascript")
        self.assertIn("function multiply(x, y) {", data.get("code", ""))

    def test_8_empty_source_validation(self):
        """Test POST /api/translate with empty source string returns HTTP 400."""
        payload = {
            "source": "   ",
            "target_language": "java",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("source must not be empty", data.get("error", ""))

    def test_9_missing_source_validation(self):
        """Test POST /api/translate without source returns HTTP 400."""
        payload = {
            "target_language": "java",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("source must not be empty", data.get("error", ""))

    def test_10_missing_target_language_validation(self):
        """Test POST /api/translate without target_language returns HTTP 400."""
        payload = {
            "source": "def add(a, b): return a + b",
            "target_language": "",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("target_language must not be empty", data.get("error", ""))

    def test_11_invalid_python_syntax_error(self):
        """Test POST /api/translate with invalid Python syntax returns HTTP 400."""
        payload = {
            "source": "def bad_syntax(:",
            "target_language": "java",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("syntax error", data.get("error", "").lower())

    def test_12_unsupported_target_language(self):
        """Test POST /api/translate with unsupported target language returns HTTP 400."""
        payload = {
            "source": "def add(a, b): return a + b",
            "target_language": "ruby",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("Unsupported target language", data.get("error", ""))

    def test_13_response_json_structure(self):
        """Test response JSON contains exactly the expected keys."""
        payload = {
            "source": "print('hello')",
            "target_language": "javascript",
        }
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("success", data)
        self.assertIn("source_language", data)
        self.assertIn("target_language", data)
        self.assertIn("code", data)
        self.assertIn("error", data)
        self.assertEqual(data["source_language"], "python")
        self.assertEqual(data["target_language"], "javascript")
        self.assertEqual(data["code"], 'console.log("hello");')
        self.assertIsNone(data["error"])

    def test_14_translation_error_returns_422(self):
        """Test that translation errors (e.g. UnsupportedIRNodeError) return HTTP 422."""
        with patch("app.main.engine.translate", side_effect=UnsupportedIRNodeError("UnknownCustomNode")):
            payload = {
                "source": "def foo(): pass",
                "target_language": "javascript",
            }
            response = self.client.post("/api/translate", json=payload)
            self.assertEqual(response.status_code, 422)
            data = response.json()
            self.assertFalse(data.get("success"))
            self.assertIn("Translation error", data.get("error", ""))

    def test_15_end_to_end_pipeline_all_targets(self):
        """
        Test end-to-end translation pipeline for Python input across all 3 targets:
        Python -> AST -> IR -> TranslationEngine -> Java / C++ / JavaScript
        """
        python_input = """def calculate_area(width: int, height: int) -> int:
    area: int = width * height
    return area

print(calculate_area(5, 10))
"""
        res_java = self.client.post("/api/translate", json={"source": python_input, "target_language": "java"})
        self.assertEqual(res_java.status_code, 200)
        self.assertIn("public class Main", res_java.json()["code"])
        self.assertIn("public static int calculate_area(int width, int height)", res_java.json()["code"])

        res_cpp = self.client.post("/api/translate", json={"source": python_input, "target_language": "cpp"})
        self.assertEqual(res_cpp.status_code, 200)
        self.assertIn("int calculate_area(int width, int height)", res_cpp.json()["code"])
        self.assertIn("int main()", res_cpp.json()["code"])

        res_js = self.client.post("/api/translate", json={"source": python_input, "target_language": "javascript"})
        self.assertEqual(res_js.status_code, 200)
        self.assertIn("function calculate_area(width, height)", res_js.json()["code"])
        self.assertIn("console.log(calculate_area(5, 10));", res_js.json()["code"])

    def test_16_oversized_source_code_rejected(self):
        """Test POST /api/translate with oversized payload (>100k chars) returns HTTP 400."""
        oversized = "x = 1\n" * 25000
        response = self.client.post("/api/translate", json={"source": oversized, "target_language": "javascript"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("exceeds maximum allowed length", data.get("error", ""))

    def test_17_builtins_via_api(self):
        """Test translating built-in math and string functions via API."""
        src = "def test_builtins(x: int) -> int:\n    return abs(x) + min(x, 10)\n"
        res_cpp = self.client.post("/api/translate", json={"source": src, "target_language": "cpp"})
        self.assertEqual(res_cpp.status_code, 200)
        self.assertIn("std::abs(x)", res_cpp.json()["code"])
        self.assertIn("std::min(x, 10)", res_cpp.json()["code"])

    def test_18_classes_and_oop_via_api(self):
        """Test translating Python class / OOP constructs via API."""
        src = """class User:
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name
"""
        res_js = self.client.post("/api/translate", json={"source": src, "target_language": "javascript"})
        self.assertEqual(res_js.status_code, 200)
        self.assertIn("class User {", res_js.json()["code"])
        self.assertIn("constructor(name) {", res_js.json()["code"])
        self.assertIn("this.name = name;", res_js.json()["code"])

    def test_19_exceptions_via_api(self):
        """Test translating try/except/finally via API."""
        src = """def run():
    try:
        x = 1
    except Exception as e:
        print("error")
"""
        res_cpp = self.client.post("/api/translate", json={"source": src, "target_language": "cpp"})
        self.assertEqual(res_cpp.status_code, 200)
        self.assertIn("try {", res_cpp.json()["code"])
        self.assertIn("catch (const std::exception& e) {", res_cpp.json()["code"])

    def test_20_list_comprehension_via_api(self):
        """Test translating list comprehensions via API."""
        src = "squares = [x * 2 for x in range(5)]\n"
        res_java = self.client.post("/api/translate", json={"source": src, "target_language": "java"})
        self.assertEqual(res_java.status_code, 200)
        self.assertIn("squares.add(x * 2);", res_java.json()["code"])


if __name__ == "__main__":
    unittest.main()
