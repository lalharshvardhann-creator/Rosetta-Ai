import ast
from typing import Any, Dict, List


class PythonASTAnalyzer(ast.NodeVisitor):

    def __init__(self):
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.variables: List[Dict[str, Any]] = []
        self.imports: List[Dict[str, Any]] = []
        self.control_flow: List[Dict[str, Any]] = []
        self.expressions: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []

    def _safe_unparse(self, node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return str(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool):
        params = [arg.arg for arg in node.args.args]
        if node.args.vararg:
            params.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            params.append(f"**{node.args.kwarg.arg}")

        returns = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if child.value is not None:
                    returns.append(self._safe_unparse(child.value))
                else:
                    returns.append("None")

        func_info = {
            "name": node.name,
            "parameters": params,
            "returns": returns,
            "is_async": is_async,
            "line_number": node.lineno,
            "docstring": ast.get_docstring(node),
        }
        self.functions.append(func_info)

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [self._safe_unparse(base) for base in node.bases]

        methods = [
            n.name
            for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        class_info = {
            "name": node.name,
            "bases": bases,
            "methods": methods,
            "line_number": node.lineno,
            "docstring": ast.get_docstring(node),
        }
        self.classes.append(class_info)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        targets = [self._safe_unparse(t) for t in node.targets]
        value_str = self._safe_unparse(node.value)

        for target in targets:
            self.variables.append({
                "name": target,
                "value": value_str,
                "line_number": node.lineno,
            })
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        target = self._safe_unparse(node.target)
        value_str = self._safe_unparse(node.value) if node.value else None
        annotation_str = self._safe_unparse(node.annotation)

        self.variables.append({
            "name": target,
            "value": value_str,
            "type_annotation": annotation_str,
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        names = [
            f"{alias.name} as {alias.asname}" if alias.asname else alias.name
            for alias in node.names
        ]
        self.imports.append({
            "type": "import",
            "module": None,
            "names": names,
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        names = [
            f"{alias.name} as {alias.asname}" if alias.asname else alias.name
            for alias in node.names
        ]
        self.imports.append({
            "type": "import_from",
            "module": node.module,
            "names": names,
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.control_flow.append({
            "type": "if",
            "condition": self._safe_unparse(node.test),
            "has_else": bool(node.orelse),
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.control_flow.append({
            "type": "for",
            "target": self._safe_unparse(node.target),
            "iterator": self._safe_unparse(node.iter),
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.control_flow.append({
            "type": "while",
            "condition": self._safe_unparse(node.test),
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        op_name = node.op.__class__.__name__
        self.expressions.append({
            "type": "binary_operation",
            "operator": op_name,
            "code": self._safe_unparse(node),
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        ops = [op.__class__.__name__ for op in node.ops]
        self.expressions.append({
            "type": "comparison",
            "operators": ops,
            "code": self._safe_unparse(node),
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = self._safe_unparse(node.func)
        args = [self._safe_unparse(arg) for arg in node.args]
        self.expressions.append({
            "type": "function_call",
            "function": func_name,
            "arguments": args,
            "code": self._safe_unparse(node),
            "line_number": node.lineno,
        })
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        const_type = type(node.value).__name__
        self.constants.append({
            "type": const_type,
            "value": node.value,
            "line_number": node.lineno,
        })
        self.generic_visit(node)


def analyze_python_code(source_code: str) -> Dict[str, Any]:
    """
    Parses Python source code into an Abstract Syntax Tree (AST) and extracts
    structural components.

    Args:
        source_code (str): The raw Python code to analyze.

    Returns:
        dict: A structured dictionary containing extracted program elements,
              or error details if syntax parsing fails.
    """
    if not source_code or not source_code.strip():
        return {
            "success": True,
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": [],
            "control_flow": [],
            "expressions": [],
            "constants": [],
        }

    try:
        tree = ast.parse(source_code)
    except SyntaxError as err:
        return {
            "success": False,
            "error": f"SyntaxError: {err.msg}",
            "line": err.lineno,
            "offset": err.offset,
            "text": err.text,
        }
    except Exception as err:
        return {
            "success": False,
            "error": f"ParseError: {str(err)}",
        }

    analyzer = PythonASTAnalyzer()
    analyzer.visit(tree)

    return {
        "success": True,
        "functions": analyzer.functions,
        "classes": analyzer.classes,
        "variables": analyzer.variables,
        "imports": analyzer.imports,
        "control_flow": analyzer.control_flow,
        "expressions": analyzer.expressions,
        "constants": analyzer.constants,
    }
