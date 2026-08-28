# Rosetta AI 🏛️⚡

> **An AI-assisted cross-language code translation system that converts Python code into Java, C++, and JavaScript while preserving program logic as closely as possible.**

---

## 📌 Project Overview

**Rosetta AI** provides a clean, fast, and student-friendly developer platform to translate Python source code into clean, idiomatic target code across **JavaScript**, **Java**, and **C++**.

Rather than relying on naive string matching or raw LLM prompts, Rosetta AI leverages a robust multi-stage compiler architecture:

```
Python Source Code
       │
       ▼
Python AST Analyzer
       │
       ▼
Intermediate Representation (IR)
       │
       ▼
TranslationEngine
       │
  ┌────┼──────────────┐
  ▼    ▼              ▼
Java  C++         JavaScript
Generator Generator Generator
```

---

## 🚀 Key Features

- **Multi-Language Translation**:
  - **JavaScript**: Idiomatic modern ES6+ functions, arrays, objects, and console output.
  - **Java**: Strongly-typed static methods, class encapsulation (`public class Main`), and standard imports.
  - **C++**: Statically typed headers (`#include <iostream>`), namespaces, and functions.
- **Python Language Support**:
  - Functions, parameters, return types, and default values.
  - Variable assignments, data types, and arithmetic operations.
  - Control flow: `if` / `elif` / `else`, `for` loops, `range()` stepping, and `while` loops.
  - Data structures: Lists, dictionaries, sets, tuples, unpacking, and comprehensions.
  - Exception handling: `try` / `except` / `else` / `finally`, specific exception types, and `raise`.
  - Object-Oriented Programming: Class definitions, `__init__` constructors, and methods.
- **🔍 Code Analysis (Big-O & Pseudocode)**:
  - Language-independent standardized pseudocode generation.
  - Asymptotic **Time Complexity** ($O(1)$, $O(\log n)$, $O(n)$, $O(n^2)$) with algorithmic explanations.
  - Auxiliary **Space Complexity** with memory footprint rationale.
- **Clean Student-Friendly Interface**:
  - Dark glassmorphic workspace with interactive code editor.
  - Side-by-side input and output editors.
  - One-click copy, keyboard shortcuts (`Ctrl+Enter` to translate), and clear loading indicators.

> [!NOTE]
> **Code Review Notice**: Generated target code provides an idiomatic structural translation of Python logic. As with all cross-language compilation tools, generated code should always be reviewed and tested with your specific test cases before production use.

---

## 🏗️ Project Structure

```
Rosetta_AI/
│
├── backend/
│   ├── app/
│   │   ├── analyzer/         # Python AST parser, pseudocode, and Big-O complexity analyzer
│   │   ├── ir/               # Intermediate Representation AST nodes & builder
│   │   ├── translation/      # TranslationEngine, BaseGenerator, Java/C++/JS generators
│   │   └── main.py           # FastAPI REST API (/api/translate, /api/analyze, /api/health)
│   ├── tests/                # Comprehensive unit, compilation & integration tests
│   └── requirements.txt      # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Translator, Hero, Navbar, HowItWorks, About, Footer
│   │   ├── App.jsx           # Main application component
│   │   └── index.css         # Clean dark mode glassmorphism UI styles
│   ├── vite.config.js        # Vite dev proxy configuration (/api -> :8000)
│   └── package.json          # Frontend dependencies and build scripts
│
└── README.md
```

---

## 🚀 Getting Started

### 1. Backend Setup & Startup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend server runs at `http://127.0.0.1:8000`.

### 2. Frontend Setup & Startup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

### 3. Production Build

```bash
cd frontend
npm run build
```

---

## 🔌 API Endpoints

### 1. Health Check
- **Endpoint**: `GET /api/health`
- **Response**:
```json
{
  "status": "ok",
  "engine": "Rosetta AI",
  "supported_languages": ["cpp", "java", "javascript"]
}
```

### 2. Code Translation
- **Endpoint**: `POST /api/translate`
- **Request Body**:
```json
{
  "source": "def add(a: int, b: int) -> int:\n    return a + b\n\nprint(add(10, 20))",
  "target_language": "javascript"
}
```
- **Response Body (Success - HTTP 200)**:
```json
{
  "success": true,
  "source_language": "python",
  "target_language": "javascript",
  "code": "function add(a, b) {\n    return a + b;\n}\n\nconsole.log(add(10, 20));",
  "error": null
}
```

### 3. Code Analysis
- **Endpoint**: `POST /api/analyze`
- **Request Body**:
```json
{
  "source": "def add(a, b):\n    return a + b"
}
```
- **Response Body (Success - HTTP 200)**:
```json
{
  "success": true,
  "pseudocode": "START\n    FUNCTION add(a, b)\n        RETURN a + b\n    END FUNCTION\nEND",
  "time_complexity": "O(1)",
  "time_explanation": "The code consists of sequential basic operations without variable loops or recursion.",
  "space_complexity": "O(1)",
  "space_explanation": "Only constant-size variables are used and no additional data structure grows with input size.",
  "error": null
}
```

---

## 🧪 Testing

### Backend Unit & Integration Tests
```bash
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

### Frontend Build Validation
```bash
cd frontend
npm run build
```
