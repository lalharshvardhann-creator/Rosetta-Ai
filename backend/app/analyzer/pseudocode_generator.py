"""
Rosetta AI - Pseudocode Generator
---------------------------------
Converts Python Abstract Syntax Trees (AST) into clean, language-independent,
readable algorithmic pseudocode focusing on logic rather than Python-specific syntax.
"""

import ast
from typing import List, Optional


class PseudocodeGenerator:
    """
    Translates Python AST into structured, standardized algorithmic pseudocode.
    """

    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size

    def generate(self, source_code: str) -> str:
        """
        Parses Python code and generates standardized pseudocode.
        """
        if not source_code or not source_code.strip():
            return "START\nEND"

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            line_info = f" on line {e.lineno}" if e.lineno else ""
            raise ValueError(f"Syntax error{line_info}: {e.msg or str(e)}")

        lines = ["START"]
        body_lines = self._generate_statements(tree.body, level=1)
        if body_lines:
            lines.extend(body_lines)
        else:
            lines.append(self._indent("PASS", 1))
        lines.append("END")
        return "\n".join(lines)

    def _indent(self, text: str, level: int) -> str:
        return (" " * (self.indent_size * level)) + text

    def _generate_statements(self, statements: List[ast.stmt], level: int) -> List[str]:
        result: List[str] = []
        for stmt in statements:
            stmt_lines = self._generate_statement(stmt, level)
            result.extend(stmt_lines)
        return result

    def _generate_statement(self, stmt: ast.stmt, level: int) -> List[str]:
        if isinstance(stmt, ast.FunctionDef) or isinstance(stmt, ast.AsyncFunctionDef):
            return self._format_function(stmt, level)
        elif isinstance(stmt, ast.ClassDef):
            return self._format_class(stmt, level)
        elif isinstance(stmt, ast.Return):
            return self._format_return(stmt, level)
        elif isinstance(stmt, ast.Assign):
            return self._format_assign(stmt, level)
        elif isinstance(stmt, ast.AugAssign):
            return self._format_aug_assign(stmt, level)
        elif isinstance(stmt, ast.AnnAssign):
            return self._format_ann_assign(stmt, level)
        elif isinstance(stmt, ast.For) or isinstance(stmt, ast.AsyncFor):
            return self._format_for(stmt, level)
        elif isinstance(stmt, ast.While):
            return self._format_while(stmt, level)
        elif isinstance(stmt, ast.If):
            return self._format_if(stmt, level)
        elif isinstance(stmt, ast.Expr):
            return self._format_expr_stmt(stmt, level)
        elif isinstance(stmt, ast.Pass):
            return [self._indent("PASS", level)]
        elif isinstance(stmt, ast.Break):
            return [self._indent("BREAK", level)]
        elif isinstance(stmt, ast.Continue):
            return [self._indent("CONTINUE", level)]
        elif isinstance(stmt, ast.Assert):
            cond = self._format_expr(stmt.test)
            return [self._indent(f"ASSERT {cond}", level)]
        elif isinstance(stmt, ast.Raise):
            exc = self._format_expr(stmt.exc) if stmt.exc else ""
            return [self._indent(f"RAISE {exc}".strip(), level)]
        elif isinstance(stmt, ast.Try):
            return self._format_try(stmt, level)
        elif isinstance(stmt, ast.Import) or isinstance(stmt, ast.ImportFrom):
            return []
        elif isinstance(stmt, ast.Global) or isinstance(stmt, ast.Nonlocal):
            names = ", ".join(stmt.names)
            return [self._indent(f"GLOBAL {names}", level)]
        else:
            return [self._indent(self._format_expr_fallback(stmt), level)]


    def _format_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, level: int) -> List[str]:
        params = [arg.arg for arg in node.args.args]
        if node.args.vararg:
            params.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            params.append(f"**{node.args.kwarg.arg}")

        params_str = ", ".join(params)
        prefix = "ASYNC FUNCTION" if isinstance(node, ast.AsyncFunctionDef) else "FUNCTION"
        lines = [self._indent(f"{prefix} {node.name}({params_str})", level)]

        body_lines = self._generate_statements(node.body, level + 1)
        if body_lines:
            lines.extend(body_lines)
        else:
            lines.append(self._indent("PASS", level + 1))

        lines.append(self._indent("END FUNCTION", level))
        return lines

    def _format_class(self, node: ast.ClassDef, level: int) -> List[str]:
        bases = [self._format_expr(base) for base in node.bases]
        bases_str = f" EXTENDS {', '.join(bases)}" if bases else ""
        lines = [self._indent(f"CLASS {node.name}{bases_str}", level)]

        body_lines = self._generate_statements(node.body, level + 1)
        if body_lines:
            lines.extend(body_lines)
        else:
            lines.append(self._indent("PASS", level + 1))

        lines.append(self._indent("END CLASS", level))
        return lines

    def _format_return(self, node: ast.Return, level: int) -> List[str]:
        if node.value is None:
            return [self._indent("RETURN", level)]
        val_str = self._format_expr(node.value)
        return [self._indent(f"RETURN {val_str}", level)]

    def _format_assign(self, node: ast.Assign, level: int) -> List[str]:
        targets = [self._format_expr(t) for t in node.targets]
        val_str = self._format_expr(node.value)
        target_str = ", ".join(targets)
        return [self._indent(f"SET {target_str} = {val_str}", level)]

    def _format_aug_assign(self, node: ast.AugAssign, level: int) -> List[str]:
        target = self._format_expr(node.target)
        val = self._format_expr(node.value)
        op_symbol = self._get_operator_symbol(node.op)
        return [self._indent(f"SET {target} = {target} {op_symbol} {val}", level)]

    def _format_ann_assign(self, node: ast.AnnAssign, level: int) -> List[str]:
        target = self._format_expr(node.target)
        if node.value is not None:
            val_str = self._format_expr(node.value)
            return [self._indent(f"SET {target} = {val_str}", level)]
        return [self._indent(f"DECLARE {target}", level)]

    def _format_for(self, node: ast.For | ast.AsyncFor, level: int) -> List[str]:
        target = self._format_expr(node.target)
        is_range, range_desc = self._extract_range_bounds(node.iter)
        if is_range:
            header = f"FOR {target} {range_desc}"
        else:
            iter_str = self._format_expr(node.iter)
            header = f"FOR EACH {target} IN {iter_str}"

        lines = [self._indent(header, level)]
        body_lines = self._generate_statements(node.body, level + 1)
        if body_lines:
            lines.extend(body_lines)
        else:
            lines.append(self._indent("PASS", level + 1))
        lines.append(self._indent("END FOR", level))

        if node.orelse:
            lines.append(self._indent("IF NO BREAK THEN", level))
            lines.extend(self._generate_statements(node.orelse, level + 1))
            lines.append(self._indent("END IF", level))

        return lines

    def _extract_range_bounds(self, iter_node: ast.expr) -> tuple[bool, str]:
        """Checks if iter_node is range(...) and formats 'FROM start TO end [STEP step]'."""
        if not isinstance(iter_node, ast.Call):
            return False, ""
        if isinstance(iter_node.func, ast.Name) and iter_node.func.id == "range":
            args = iter_node.args
            if len(args) == 1:
                stop_node = args[0]
                if isinstance(stop_node, ast.Constant) and isinstance(stop_node.value, int):
                    return True, f"FROM 0 TO {stop_node.value - 1}"
                else:
                    stop_str = self._format_expr(stop_node)
                    return True, f"FROM 0 TO {stop_str} - 1"
            elif len(args) == 2:
                start_str = self._format_expr(args[0])
                stop_node = args[1]
                if isinstance(stop_node, ast.Constant) and isinstance(stop_node.value, int):
                    return True, f"FROM {start_str} TO {stop_node.value - 1}"
                else:
                    stop_str = self._format_expr(stop_node)
                    return True, f"FROM {start_str} TO {stop_str} - 1"
            elif len(args) == 3:
                start_str = self._format_expr(args[0])
                stop_node = args[1]
                step_str = self._format_expr(args[2])
                if isinstance(stop_node, ast.Constant) and isinstance(stop_node.value, int):
                    return True, f"FROM {start_str} TO {stop_node.value - 1} STEP {step_str}"
                else:
                    stop_str = self._format_expr(stop_node)
                    return True, f"FROM {start_str} TO {stop_str} - 1 STEP {step_str}"
        return False, ""

    def _format_while(self, node: ast.While, level: int) -> List[str]:
        cond_str = self._format_expr(node.test)
        lines = [self._indent(f"WHILE {cond_str} DO", level)]
        body_lines = self._generate_statements(node.body, level + 1)
        if body_lines:
            lines.extend(body_lines)
        else:
            lines.append(self._indent("PASS", level + 1))
        lines.append(self._indent("END WHILE", level))
        return lines

    def _format_if(self, node: ast.If, level: int) -> List[str]:
        cond_str = self._format_expr(node.test)
        lines = [self._indent(f"IF {cond_str} THEN", level)]
        body_lines = self._generate_statements(node.body, level + 1)
        if body_lines:
            lines.extend(body_lines)
        else:
            lines.append(self._indent("PASS", level + 1))

        current_else = node.orelse
        while current_else:
            if len(current_else) == 1 and isinstance(current_else[0], ast.If):
                elif_node = current_else[0]
                elif_cond = self._format_expr(elif_node.test)
                lines.append(self._indent(f"ELSE IF {elif_cond} THEN", level))
                elif_body = self._generate_statements(elif_node.body, level + 1)
                if elif_body:
                    lines.extend(elif_body)
                else:
                    lines.append(self._indent("PASS", level + 1))
                current_else = elif_node.orelse
            else:
                lines.append(self._indent("ELSE", level))
                else_body = self._generate_statements(current_else, level + 1)
                if else_body:
                    lines.extend(else_body)
                else:
                    lines.append(self._indent("PASS", level + 1))
                break

        lines.append(self._indent("END IF", level))
        return lines

    def _format_try(self, node: ast.Try, level: int) -> List[str]:
        lines = [self._indent("TRY", level)]
        lines.extend(self._generate_statements(node.body, level + 1))
        for handler in node.handlers:
            exc_type = self._format_expr(handler.type) if handler.type else "Exception"
            alias_str = f" AS {handler.name}" if handler.name else ""
            lines.append(self._indent(f"CATCH {exc_type}{alias_str}", level))
            lines.extend(self._generate_statements(handler.body, level + 1))
        if node.orelse:
            lines.append(self._indent("IF NO ERROR THEN", level))
            lines.extend(self._generate_statements(node.orelse, level + 1))
        if node.finalbody:
            lines.append(self._indent("FINALLY", level))
            lines.extend(self._generate_statements(node.finalbody, level + 1))
        lines.append(self._indent("END TRY", level))
        return lines

    def _format_expr_stmt(self, node: ast.Expr, level: int) -> List[str]:
        val = node.value
        if isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id == "print":
            args_str = ", ".join(self._format_expr(arg) for arg in val.args)
            return [self._indent(f"PRINT {args_str}".strip(), level)]
        elif isinstance(val, ast.Yield):
            y_val = self._format_expr(val.value) if val.value else ""
            return [self._indent(f"YIELD {y_val}".strip(), level)]
        else:
            expr_str = self._format_expr(val)
            return [self._indent(expr_str, level)]


    def _format_expr(self, node: Optional[ast.AST]) -> str:
        if node is None:
            return ""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            if node.value is None:
                return "NULL"
            elif isinstance(node.value, bool):
                return "TRUE" if node.value else "FALSE"
            elif isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)
        elif isinstance(node, ast.BinOp):
            left = self._format_expr(node.left)
            op = self._get_operator_symbol(node.op)
            right = self._format_expr(node.right)
            return f"{left} {op} {right}"
        elif isinstance(node, ast.UnaryOp):
            op = self._get_unary_operator_symbol(node.op)
            operand = self._format_expr(node.operand)
            return f"{op}{operand}"
        elif isinstance(node, ast.BoolOp):
            op_name = "AND" if isinstance(node.op, ast.And) else "OR"
            values = [self._format_expr(v) for v in node.values]
            return f" {op_name} ".join(values)
        elif isinstance(node, ast.Compare):
            left = self._format_expr(node.left)
            parts = [left]
            for op, comparator in zip(node.ops, node.comparators):
                op_str = self._get_comparison_operator_symbol(op)
                comp_str = self._format_expr(comparator)
                parts.append(f"{op_str} {comp_str}")
            return " ".join(parts)
        elif isinstance(node, ast.Call):
            func_name = self._format_expr(node.func)
            if func_name == "print":
                args_str = ", ".join(self._format_expr(arg) for arg in node.args)
                return f"PRINT({args_str})"
            args_str = ", ".join(self._format_expr(arg) for arg in node.args)
            return f"{func_name}({args_str})"
        elif isinstance(node, ast.Attribute):
            val = self._format_expr(node.value)
            return f"{val}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            val = self._format_expr(node.value)
            sl = self._format_expr(node.slice)
            return f"{val}[{sl}]"
        elif isinstance(node, ast.Slice):
            lower = self._format_expr(node.lower) if node.lower else ""
            upper = self._format_expr(node.upper) if node.upper else ""
            step = f":{self._format_expr(node.step)}" if node.step else ""
            return f"{lower}:{upper}{step}"
        elif isinstance(node, ast.List):
            elems = ", ".join(self._format_expr(e) for e in node.elts)
            return f"[{elems}]"
        elif isinstance(node, ast.Tuple):
            elems = ", ".join(self._format_expr(e) for e in node.elts)
            return f"({elems})"
        elif isinstance(node, ast.Set):
            elems = ", ".join(self._format_expr(e) for e in node.elts)
            return f"{{{elems}}}"
        elif isinstance(node, ast.Dict):
            items = []
            for k, v in zip(node.keys, node.values):
                k_str = self._format_expr(k) if k else "..."
                v_str = self._format_expr(v)
                items.append(f"{k_str}: {v_str}")
            return f"{{{', '.join(items)}}}"
        elif isinstance(node, ast.IfExp):
            test = self._format_expr(node.test)
            body = self._format_expr(node.body)
            orelse = self._format_expr(node.orelse)
            return f"({body} IF {test} ELSE {orelse})"
        elif isinstance(node, ast.ListComp):
            elt = self._format_expr(node.elt)
            gen = node.generators[0] if node.generators else None
            if gen:
                tgt = self._format_expr(gen.target)
                it = self._format_expr(gen.iter)
                cond_str = f" WHERE {self._format_expr(gen.ifs[0])}" if gen.ifs else ""
                return f"[EACH {elt} FOR {tgt} IN {it}{cond_str}]"
            return f"[{elt}]"
        elif isinstance(node, ast.Lambda):
            params = ", ".join(a.arg for a in node.args.args)
            body = self._format_expr(node.body)
            return f"LAMBDA({params}) -> {body}"
        elif isinstance(node, ast.Yield):
            val = self._format_expr(node.value) if node.value else ""
            return f"YIELD {val}".strip()
        else:
            return self._format_expr_fallback(node)

    def _format_expr_fallback(self, node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return str(node)

    def _get_operator_symbol(self, op: ast.operator) -> str:
        mapping: dict[type, str] = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",
            ast.Mod: "%",
            ast.Pow: "^",
            ast.BitAnd: "&",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.LShift: "<<",
            ast.RShift: ">>",
        }
        return mapping.get(type(op), "+")

    def _get_unary_operator_symbol(self, op: ast.unaryop) -> str:
        mapping: dict[type, str] = {
            ast.UAdd: "+",
            ast.USub: "-",
            ast.Not: "NOT ",
            ast.Invert: "~",
        }
        return mapping.get(type(op), "-")

    def _get_comparison_operator_symbol(self, op: ast.cmpop) -> str:
        mapping: dict[type, str] = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "IS",
            ast.IsNot: "IS NOT",
            ast.In: "IN",
            ast.NotIn: "NOT IN",
        }
        return mapping.get(type(op), "==")


def generate_pseudocode(source_code: str) -> str:
    """
    Convenience function to generate pseudocode from Python source code.
    """
    generator = PseudocodeGenerator()
    return generator.generate(source_code)
