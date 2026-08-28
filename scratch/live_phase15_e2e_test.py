"""
Rosetta AI - Phase 15 End-to-End Frontend ↔ Backend Integration Verification
-----------------------------------------------------------------------------
Performs full verification of the frontend/backend integration contract:
1. Tests POST /api/translate with canonical Python input:
   def add(a, b):
       return a + b
2. Verifies translation across JavaScript, Java, and C++.
3. Verifies error states and UI contract compliance.
"""

import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.main import app

client = TestClient(app)

def test_phase15_e2e():
    print("=" * 60)
    print("PHASE 15: FRONTEND <-> BACKEND END-TO-END INTEGRATION TEST")
    print("=" * 60)

    # 1. Health check
    health_res = client.get("/api/health")
    print(f"GET /api/health -> HTTP {health_res.status_code}")
    assert health_res.status_code == 200
    health_data = health_res.json()
    print(f"Supported languages: {health_data.get('supported_languages')}")
    assert "javascript" in health_data.get("supported_languages")
    assert "java" in health_data.get("supported_languages")
    assert "cpp" in health_data.get("supported_languages")

    # 2. Canonical Translation Test: def add(a, b): return a + b -> JavaScript
    payload_js = {
        "source": "def add(a, b):\n    return a + b",
        "target_language": "javascript"
    }
    print(f"\nPOST /api/translate (JavaScript payload): {payload_js}")
    res_js = client.post("/api/translate", json=payload_js)
    print(f"Response HTTP status: {res_js.status_code}")
    assert res_js.status_code == 200
    data_js = res_js.json()
    print(f"Response JSON: {data_js}")
    assert data_js["success"] is True
    assert "function add(a, b)" in data_js["code"]
    assert "return a + b;" in data_js["code"]
    print("[SUCCESS] JavaScript translation contract validated.")

    # 3. Canonical Translation Test -> Java
    payload_java = {
        "source": "def add(a: int, b: int) -> int:\n    return a + b",
        "target_language": "java"
    }
    print(f"\nPOST /api/translate (Java payload): {payload_java}")
    res_java = client.post("/api/translate", json=payload_java)
    print(f"Response HTTP status: {res_java.status_code}")
    assert res_java.status_code == 200
    data_java = res_java.json()
    assert data_java["success"] is True
    assert "public static int add(int a, int b)" in data_java["code"]
    print("[SUCCESS] Java translation contract validated.")

    # 4. Canonical Translation Test -> C++
    payload_cpp = {
        "source": "def add(a: int, b: int) -> int:\n    return a + b",
        "target_language": "cpp"
    }
    print(f"\nPOST /api/translate (C++ payload): {payload_cpp}")
    res_cpp = client.post("/api/translate", json=payload_cpp)
    print(f"Response HTTP status: {res_cpp.status_code}")
    assert res_cpp.status_code == 200
    data_cpp = res_cpp.json()
    assert data_cpp["success"] is True
    assert "int add(int a, int b)" in data_cpp["code"]
    print("[SUCCESS] C++ translation contract validated.")

    # 5. Error state validation: Syntax Error
    payload_bad = {
        "source": "def broken_code(",
        "target_language": "javascript"
    }
    print(f"\nPOST /api/translate (Syntax Error payload): {payload_bad}")
    res_bad = client.post("/api/translate", json=payload_bad)
    print(f"Response HTTP status: {res_bad.status_code}")
    assert res_bad.status_code == 400
    data_bad = res_bad.json()
    assert data_bad["success"] is False
    assert data_bad["error"] is not None
    print(f"Graceful error message returned: '{data_bad['error']}'")
    print("[SUCCESS] Error handling contract validated.")

    print("\n" + "=" * 60)
    print("ALL PHASE 15 END-TO-END INTEGRATION TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase15_e2e()
