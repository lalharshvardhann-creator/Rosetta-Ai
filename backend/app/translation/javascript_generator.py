from typing import Dict, List, Optional, Set

from app.ir.nodes import (
    IRAssert,
    IRAssignment,
    IRAttribute,
    IRBinaryOperation,
    IRBreak,
    IRChainedComparison,
    IRClass,
    IRConditionalExpression,
    IRConstant,
    IRContinue,
    IRDict,
    IRDictComprehension,
    IRExcept,
    IRExpressionStatement,
    IRFor,
    IRFunction,
    IRFunctionCall,
    IRGeneratorExpression,
    IRIf,
    IRImport,
    IRIsInstance,
    IRLambda,
    IRList,
    IRListComprehension,
    IRName,
    IRNode,
    IRProgram,
    IRRaise,
    IRReturn,
    IRSet,
    IRSetComprehension,
    IRSlice,
    IRStarred,
    IRSubscript,
    IRTry,
    IRTuple,
    IRTupleAssignment,
    IRUnaryOperation,
    IRVariable,
    IRWhile,
    IRYield,
)
from .base_generator import BaseCodeGenerator
from .exceptions import TranslationError
from .modules import ModuleMappingRegistry


JS_OPERATOR_MAP: Dict[str, str] = {
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "%": "%",
    "==": "===",
    "!=": "!==",
    "===": "===",
    "!==": "!==",
    "<": "<",
    "<=": "<=",
    ">": ">",
    ">=": ">=",
    "and": "&&",
    "&&": "&&",
    "or": "||",
    "||": "||",
    "not": "!",
    "!": "!",
    "~": "~",
    "&": "&",
    "|": "|",
    "^": "^",
    "<<": "<<",
    ">>": ">>",
    "**": "**",
}

JS_KEYWORDS = {
    "abstract", "arguments", "async", "await", "boolean", "break", "byte",
    "case", "catch", "char", "class", "const", "continue", "debugger",
    "default", "delete", "do", "double", "else", "enum", "eval", "export",
    "extends", "false", "final", "finally", "float", "for", "function",
    "goto", "if", "implements", "import", "in", "instanceof", "int",
    "interface", "let", "long", "native", "new", "null", "package",
    "private", "protected", "public", "return", "short", "static",
    "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "true", "try", "typeof", "var", "void", "volatile",
    "while", "with", "yield", "undefined", "NaN", "Infinity",
}


class JavaScriptGenerator(BaseCodeGenerator):
    """
    JavaScript target-language code generator.
    Converts language-agnostic IR nodes into standard ES2020 JavaScript source code.
    """

    def __init__(self, indent_size: int = 4):
        super().__init__(indent_size=indent_size)
        self._declared_in_scope: Set[str] = set()
        self._known_classes: Set[str] = set()

    def reset_state(self) -> None:
        """Resets generator internal scope tracking state."""
        self._declared_in_scope.clear()
        self._known_classes.clear()

    def _sanitize_name(self, name: str) -> str:
        """
        Appends an underscore if the identifier collides with a JavaScript reserved keyword.
        """
        if name in JS_KEYWORDS:
            return f"{name}_"
        return name

    def generate_program(self, node: IRProgram) -> str:
        """
        Generates code for a complete JavaScript module/script.
        Emits classes, functions, and top-level standalone statements directly
        without artificial main() or class wrappers.
        """
        self.reset_state()

        for cls in node.classes:
            self._known_classes.add(self._sanitize_name(cls.name))

        content_blocks: List[str] = []

        for imp in node.imports:
            imp_code = self.generate(imp)
            if imp_code:
                content_blocks.append(imp_code)

        for cls in node.classes:
            content_blocks.append(self.generate(cls))

        for func in node.functions:
            content_blocks.append(self.generate(func))

        top_level_stmts = [
            s for s in node.statements
            if s not in node.functions and s not in node.imports and s not in node.classes
        ]
        if top_level_stmts:
            stmt_lines = []
            for stmt in top_level_stmts:
                stmt_code = self.generate(stmt)
                if stmt_code:
                    stmt_lines.append(stmt_code)
            content_blocks.append("\n".join(stmt_lines))

        return "\n\n".join(content_blocks).strip()

    def generate_import(self, node: IRImport) -> str:
        """Generates an ES module import statement."""
        if node.module == "math" or "math" in node.names:
            return ""
        if node.is_from_import and node.module:
            names_str = ", ".join(node.names)
            return f"import {{ {names_str} }} from '{node.module}';"
        mod = node.module or (node.names[0] if node.names else "")
        if not mod:
            return ""
        alias = node.alias or mod.replace(".", "_")
        return f"import * as {alias} from '{mod}';"

    def _has_yield(self, stmts: List[IRNode]) -> bool:
        """Recursively checks if a statement list contains an IRYield node."""
        for s in stmts:
            if isinstance(s, IRYield):
                return True
            if isinstance(s, IRIf):
                if self._has_yield(s.then_body) or self._has_yield(s.else_body):
                    return True
            elif isinstance(s, (IRFor, IRWhile)):
                if self._has_yield(s.body) or (hasattr(s, "else_body") and self._has_yield(s.else_body)):
                    return True
            elif isinstance(s, IRTry):
                if self._has_yield(s.body) or self._has_yield(s.finally_body) or self._has_yield(s.else_body):
                    return True
                for h in s.handlers:
                    if self._has_yield(h.body):
                        return True
            elif isinstance(s, IRExpressionStatement) and isinstance(s.expression, IRYield):
                return True
        return False

    def generate_function(self, node: IRFunction) -> str:
        """
        Generates a standard JavaScript function (or generator/async function).
        Manages parameter scopes and default arguments to prevent parameter redeclarations in the body.
        """
        prev_declared = set(self._declared_in_scope)
        self._declared_in_scope.clear()

        params_str_list = []
        defaults = getattr(node, "default_values", {}) or {}
        for param in node.parameters:
            clean_param = self._sanitize_name(param)
            self._declared_in_scope.add(clean_param)
            if param in defaults:
                def_val = self.generate(defaults[param])
                params_str_list.append(f"{clean_param} = {def_val}")
            else:
                params_str_list.append(clean_param)

        params_str = ", ".join(params_str_list)
        func_name = self._sanitize_name(node.name)
        async_prefix = "async " if getattr(node, "is_async", False) else ""
        gen_star = "*" if self._has_yield(node.body) else ""

        header = f"{self.get_indent()}{async_prefix}function{gen_star} {func_name}({params_str}) {{"

        self.indent()
        body_lines: List[str] = []
        for stmt in node.body:
            stmt_code = self.generate(stmt)
            if stmt_code:
                if not stmt_code.startswith(" "):
                    stmt_code = f"{self.get_indent()}{stmt_code}"
                body_lines.append(stmt_code)
        self.dedent()

        self._declared_in_scope = prev_declared

        if not body_lines:
            body_str = f"{self.get_indent()}    // Empty body"
        else:
            body_str = "\n".join(body_lines)

        return f"{header}\n{body_str}\n{self.get_indent()}}}"

    def generate_class(self, node: IRClass) -> str:
        """Generates an ES6 JavaScript class definition with methods."""
        class_name = self._sanitize_name(node.name)
        self._known_classes.add(class_name)
        extends_clause = f" extends {node.bases[0]}" if node.bases else ""
        header = f"{self.get_indent()}class {class_name}{extends_clause} {{"

        self.indent()
        body_lines: List[str] = []

        methods = getattr(node, "methods", []) or []
        for method in methods:
            prev_declared = set(self._declared_in_scope)
            self._declared_in_scope.clear()

            method_params = []
            for param in method.parameters:
                if param in ("self", "this"):
                    continue
                clean_p = self._sanitize_name(param)
                self._declared_in_scope.add(clean_p)
                method_params.append(clean_p)

            params_str = ", ".join(method_params)
            m_name = self._sanitize_name(method.name)
            if m_name == "__init__":
                m_name = "constructor"

            async_prefix = "async " if getattr(method, "is_async", False) else ""
            gen_star = "* " if self._has_yield(method.body) and m_name != "constructor" else ""
            m_header = f"{self.get_indent()}{async_prefix}{gen_star}{m_name}({params_str}) {{"

            self.indent()
            m_body_lines = []
            for stmt in method.body:
                stmt_code = self.generate(stmt)
                if stmt_code:
                    if not stmt_code.startswith(" "):
                        stmt_code = f"{self.get_indent()}{stmt_code}"
                    m_body_lines.append(stmt_code)
            self.dedent()

            self._declared_in_scope = prev_declared

            m_body_str = "\n".join(m_body_lines) if m_body_lines else f"{self.get_indent()}    // Empty body"
            body_lines.append(f"{m_header}\n{m_body_str}\n{self.get_indent()}}}")

        for stmt in getattr(node, "body", []):
            if stmt not in methods:
                stmt_code = self.generate(stmt)
                if stmt_code:
                    body_lines.append(stmt_code)

        self.dedent()

        body_str = "\n\n".join(body_lines)
        return f"{header}\n{body_str}\n{self.get_indent()}}}"

    def generate_variable(self, node: IRVariable) -> str:
        """Generates a variable reference."""
        return self._sanitize_name(node.name)

    def generate_constant(self, node: IRConstant) -> str:
        """Generates a JavaScript literal constant."""
        if node.value is None:
            return "null"
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, str):
            escaped = (
                node.value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
                .replace("\r", "\\r")
            )
            return f'"{escaped}"'
        if isinstance(node.value, float):
            return str(node.value)
        return str(node.value)

    def generate_name(self, node: IRName) -> str:
        """Generates an identifier reference."""
        return self._sanitize_name(node.name)

    def generate_assignment(self, node: IRAssignment) -> str:
        """
        Generates a variable assignment statement.
        Uses 'let' for the first declaration in scope, and standard assignment for reassignments.
        """
        if node.target.startswith("self."):
            attr = self._sanitize_name(node.target[5:])
            val_str = self.generate(node.value) if node.value else "null"
            return f"this.{attr} = {val_str};"

        if isinstance(node.value, IRListComprehension):
            comp = node.value
            target_name = self._sanitize_name(node.target)
            var_name_inner = self._sanitize_name(comp.variable)
            elt_code = self.generate(comp.element)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                loop = f"for (let {var_name_inner} = 0; {var_name_inner} < {limit}; {var_name_inner}++) {{\n{self.get_indent()}    {cond_check}{target_name}.push({elt_code});\n{self.get_indent()}}}"
            else:
                iter_code = self.generate(comp.iterable)
                loop = f"for (const {var_name_inner} of {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}.push({elt_code});\n{self.get_indent()}}}"

            decl = f"let {target_name} = [];\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        if isinstance(node.value, IRSetComprehension):
            comp = node.value
            target_name = self._sanitize_name(node.target)
            var_name_inner = self._sanitize_name(comp.variable)
            elt_code = self.generate(comp.element)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                loop = f"for (let {var_name_inner} = 0; {var_name_inner} < {limit}; {var_name_inner}++) {{\n{self.get_indent()}    {cond_check}{target_name}.add({elt_code});\n{self.get_indent()}}}"
            else:
                iter_code = self.generate(comp.iterable)
                loop = f"for (const {var_name_inner} of {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}.add({elt_code});\n{self.get_indent()}}}"

            decl = f"let {target_name} = new Set();\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        if isinstance(node.value, IRDictComprehension):
            comp = node.value
            target_name = self._sanitize_name(node.target)
            k_code = self.generate(comp.key)
            v_code = self.generate(comp.value)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                var_name_inner = self._sanitize_name(comp.variable.strip(" ()"))
                loop = f"for (let {var_name_inner} = 0; {var_name_inner} < {limit}; {var_name_inner}++) {{\n{self.get_indent()}    {cond_check}{target_name}[{k_code}] = {v_code};\n{self.get_indent()}}}"
            elif "," in comp.variable:
                k_var, v_var = [self._sanitize_name(v.strip(" ()")) for v in comp.variable.split(",")]
                iter_code = self.generate(comp.iterable)
                if iter_code.endswith(".items()"):
                    clean_iter = iter_code[:-8]
                    loop_hdr = f"for (const [{k_var}, {v_var}] of Object.entries({clean_iter}))"
                elif iter_code.startswith("Object.entries"):
                    loop_hdr = f"for (const [{k_var}, {v_var}] of {iter_code})"
                else:
                    loop_hdr = f"for (const [{k_var}, {v_var}] of Object.entries({iter_code}))"
                loop = f"{loop_hdr} {{\n{self.get_indent()}    {cond_check}{target_name}[{k_code}] = {v_code};\n{self.get_indent()}}}"
            else:
                var_name_inner = self._sanitize_name(comp.variable.strip(" ()"))
                iter_code = self.generate(comp.iterable)
                loop = f"for (const {var_name_inner} of {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}[{k_code}] = {v_code};\n{self.get_indent()}}}"

            decl = f"let {target_name} = {{}};\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        var_name = self._sanitize_name(node.target)

        if node.value is None:
            if var_name in self._declared_in_scope:
                return f"{var_name};"
            self._declared_in_scope.add(var_name)
            return f"let {var_name};"

        val_str = self.generate(node.value)

        if var_name in self._declared_in_scope:
            return f"{var_name} = {val_str};"

        self._declared_in_scope.add(var_name)
        return f"let {var_name} = {val_str};"

    def generate_tuple_assignment(self, node: IRTupleAssignment) -> str:
        """Generates multiple assignment / array destructuring in JavaScript."""
        targets = [self._sanitize_name(t) for t in node.targets]
        targets_str = ", ".join(targets)
        val_str = self.generate(node.value)
        all_new = all(t not in self._declared_in_scope for t in targets)
        for t in targets:
            self._declared_in_scope.add(t)
        if all_new:
            return f"let [{targets_str}] = {val_str};"
        else:
            return f"[{targets_str}] = {val_str};"

    def generate_conditional_expression(self, node: IRConditionalExpression) -> str:
        """Generates ternary conditional expression (a ? b : c)."""
        cond = self.generate(node.condition)
        then_val = self.generate(node.then_expression)
        else_val = self.generate(node.else_expression)
        return f"({cond} ? {then_val} : {else_val})"

    def generate_return(self, node: IRReturn) -> str:
        """Generates a return statement."""
        if node.value:
            val_str = self.generate(node.value)
            return f"return {val_str};"
        return "return;"

    def generate_expression_statement(self, node: IRExpressionStatement) -> str:
        """Generates an expression statement terminated with a semicolon."""
        expr_str = self.generate(node.expression)
        if not expr_str.endswith(";"):
            return f"{expr_str};"
        return expr_str

    def generate_if(self, node: IRIf) -> str:
        """Generates an if / else statement block."""
        cond_str = self.generate(node.condition)
        indent_str = self.get_indent()

        self.indent()
        then_lines = [self.generate(s) for s in node.then_body]
        then_str = "\n".join([
            l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in then_lines
        ])
        self.dedent()

        result = f"{indent_str}if ({cond_str}) {{\n{then_str}\n{indent_str}}}"

        if node.else_body:
            self.indent()
            else_lines = [self.generate(s) for s in node.else_body]
            else_str = "\n".join([
                l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in else_lines
            ])
            self.dedent()
            result += f" else {{\n{else_str}\n{indent_str}}}"

        return result

    def _render_statement_with_flag(self, stmt: IRNode, break_flag: Optional[str]) -> str:
        """Helper to render statements while lowering break statements with a loop completion flag."""
        if isinstance(stmt, IRBreak) and break_flag:
            return f"{break_flag} = false;\n{self.get_indent()}break;"
        elif isinstance(stmt, IRIf):
            cond_str = self.generate(stmt.condition)
            self.indent()
            then_lines = [self._render_statement_with_flag(s, break_flag) for s in stmt.then_body]
            then_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in then_lines if l])
            self.dedent()
            res = f"{self.get_indent()}if ({cond_str}) {{\n{then_str}\n{self.get_indent()}}}"
            if stmt.else_body:
                self.indent()
                else_lines = [self._render_statement_with_flag(s, break_flag) for s in stmt.else_body]
                else_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in else_lines if l])
                self.dedent()
                res += f" else {{\n{else_str}\n{self.get_indent()}}}"
            return res
        return self.generate(stmt)

    def generate_for(self, node: IRFor) -> str:
        """Generates a JavaScript for loop (handles range(), enumerate(), zip(), for...of, Object.entries, and loop else)."""
        indent_str = self.get_indent()
        break_flag = "_completed" if node.else_body else None

        if "," in node.variable and isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "enumerate":
            targets = [self._sanitize_name(x.strip(" ()")) for x in node.variable.split(",")]
            idx_var, val_var = targets[0], targets[1]
            coll_str = self.generate(node.iterable.arguments[0])
            loop_header = f"for (let {idx_var} = 0; {idx_var} < {coll_str}.length; {idx_var}++)"
            self.indent()
            body_lines = [f"const {val_var} = {coll_str}[{idx_var}];"]
            self._declared_in_scope.add(idx_var)
            self._declared_in_scope.add(val_var)
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
            body_str = "\n".join(body_lines)
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        elif "," in node.variable and isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "zip":
            targets = [self._sanitize_name(x.strip(" ()")) for x in node.variable.split(",")]
            var_a, var_b = targets[0], targets[1]
            xs_str = self.generate(node.iterable.arguments[0])
            ys_str = self.generate(node.iterable.arguments[1])
            idx_var = "_zip_idx"
            loop_header = f"for (let {idx_var} = 0; {idx_var} < Math.min({xs_str}.length, {ys_str}.length); {idx_var}++)"
            self.indent()
            body_lines = [
                f"const {var_a} = {xs_str}[{idx_var}];",
                f"const {var_b} = {ys_str}[{idx_var}];",
            ]
            self._declared_in_scope.add(var_a)
            self._declared_in_scope.add(var_b)
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
            body_str = "\n".join(body_lines)
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        elif "," in node.variable:
            targets = [self._sanitize_name(x.strip(" ()")) for x in node.variable.split(",")]
            k_var, v_var = targets[0], targets[1]
            iter_str = self.generate(node.iterable)
            if iter_str.endswith(".items()"):
                clean_iter = iter_str[:-8]
                loop_header = f"for (const [{k_var}, {v_var}] of Object.entries({clean_iter}))"
            elif iter_str.startswith("Object.entries"):
                loop_header = f"for (const [{k_var}, {v_var}] of {iter_str})"
            else:
                loop_header = f"for (const [{k_var}, {v_var}] of Object.entries({iter_str}))"
            self._declared_in_scope.add(k_var)
            self._declared_in_scope.add(v_var)
            self.indent()
            body_lines = [
                (self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s))
                for s in node.body
            ]
            body_str = "\n".join([
                l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l
            ])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        elif isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "range":
            var_name = self._sanitize_name(node.variable)
            args = node.iterable.arguments
            if len(args) == 1:
                start_val = "0"
                stop_val = self.generate(args[0])
                loop_header = f"for (let {var_name} = {start_val}; {var_name} < {stop_val}; {var_name}++)"
            elif len(args) == 2:
                start_val = self.generate(args[0])
                stop_val = self.generate(args[1])
                loop_header = f"for (let {var_name} = {start_val}; {var_name} < {stop_val}; {var_name}++)"
            elif len(args) >= 3:
                start_val = self.generate(args[0])
                stop_val = self.generate(args[1])
                step_val = self.generate(args[2])
                if step_val.strip().startswith("-"):
                    loop_header = f"for (let {var_name} = {start_val}; {var_name} > {stop_val}; {var_name} += {step_val})"
                else:
                    loop_header = f"for (let {var_name} = {start_val}; {var_name} < {stop_val}; {var_name} += {step_val})"
            else:
                start_val = "0"
                stop_val = "0"
                loop_header = f"for (let {var_name} = {start_val}; {var_name} < {stop_val}; {var_name}++)"

            self._declared_in_scope.add(var_name)
            self.indent()
            body_lines = [
                (self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s))
                for s in node.body
            ]
            body_str = "\n".join([
                l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l
            ])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"
        else:
            var_name = self._sanitize_name(node.variable)
            iter_str = self.generate(node.iterable)
            loop_header = f"for (const {var_name} of {iter_str})"
            self._declared_in_scope.add(var_name)
            self.indent()
            body_lines = [
                (self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s))
                for s in node.body
            ]
            body_str = "\n".join([
                l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l
            ])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        if node.else_body:
            self.indent()
            else_lines = [self.generate(s) for s in node.else_body]
            else_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in else_lines if l])
            self.dedent()
            return f"{indent_str}let _completed = true;\n{loop_code}\n{indent_str}if (_completed) {{\n{else_str}\n{indent_str}}}"

        return loop_code

    def generate_while(self, node: IRWhile) -> str:
        """Generates a JavaScript while loop (including while/else lowering)."""
        indent_str = self.get_indent()
        cond_str = self.generate(node.condition)
        break_flag = "_completed" if node.else_body else None

        self.indent()
        body_lines = [
            (self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s))
            for s in node.body
        ]
        body_str = "\n".join([
            l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l
        ])
        self.dedent()

        loop_code = f"{indent_str}while ({cond_str}) {{\n{body_str}\n{indent_str}}}"

        if node.else_body:
            self.indent()
            else_lines = [self.generate(s) for s in node.else_body]
            else_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in else_lines if l])
            self.dedent()
            return f"{indent_str}let _completed = true;\n{loop_code}\n{indent_str}if (_completed) {{\n{else_str}\n{indent_str}}}"

        return loop_code

    def generate_break(self, node: IRBreak) -> str:
        """Generates a JavaScript break statement."""
        return "break;"

    def generate_continue(self, node: IRContinue) -> str:
        """Generates a JavaScript continue statement."""
        return "continue;"

    def generate_assert(self, node: IRAssert) -> str:
        """Generates a JavaScript assertion statement."""
        indent_str = self.get_indent()
        cond_str = self.generate(node.condition)
        if node.message:
            msg_str = self.generate(node.message)
            return f"{indent_str}if (!({cond_str})) throw new Error({msg_str});"
        return f"{indent_str}if (!({cond_str})) throw new Error(\"Assertion failed\");"

    def generate_yield(self, node: IRYield) -> str:
        """Generates a JavaScript yield expression."""
        val_str = self.generate(node.value) if node.value else ""
        return f"yield {val_str};" if val_str else "yield;"

    def generate_generator_expression(self, node: IRGeneratorExpression) -> str:
        """Generates a JavaScript Array pipeline from a generator expression."""
        var_name = self._sanitize_name(node.variable.strip(" ()"))
        elt_str = self.generate(node.element)
        iter_str = self.generate(node.iterable)
        if node.condition:
            cond_str = self.generate(node.condition)
            return f"{iter_str}.filter({var_name} => {cond_str}).map({var_name} => {elt_str})"
        return f"{iter_str}.map({var_name} => {elt_str})"

    def generate_starred(self, node: IRStarred) -> str:
        """Generates a JavaScript spread expression (...val)."""
        val_str = self.generate(node.value)
        return f"...{val_str}"

    def generate_isinstance(self, node: IRIsInstance) -> str:
        """Generates a JavaScript type check expression."""
        expr_str = self.generate(node.expression)
        type_name = node.type_name
        if type_name in ("int", "float"):
            return f"(typeof {expr_str} === 'number')"
        elif type_name == "str":
            return f"(typeof {expr_str} === 'string')"
        elif type_name == "bool":
            return f"(typeof {expr_str} === 'boolean')"
        elif type_name == "list":
            return f"Array.isArray({expr_str})"
        elif type_name == "dict":
            return f"({expr_str} !== null && typeof {expr_str} === 'object' && !Array.isArray({expr_str}))"
        elif type_name == "set":
            return f"({expr_str} instanceof Set)"
        return f"({expr_str} instanceof {type_name})"

    def generate_try(self, node: IRTry) -> str:
        """Generates a JavaScript try-catch-finally block (including multiple handlers and try/else)."""
        indent_str = self.get_indent()
        out = []

        if node.else_body:
            out.append(f"{indent_str}let _try_ok = true;")

        out.append(f"{indent_str}try {{")
        self.indent()
        for s in node.body:
            code = self.generate(s)
            if code:
                out.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
        self.dedent()
        out.append(f"{indent_str}}}")

        for h in node.handlers:
            alias = self._sanitize_name(h.alias) if h.alias else "e"
            out[-1] += f" catch ({alias}) {{"
            self.indent()
            if node.else_body:
                out.append(f"{self.get_indent()}_try_ok = false;")
            for s in h.body:
                code = self.generate(s)
                if code:
                    out.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
            self.dedent()
            out.append(f"{indent_str}}}")

        if node.finally_body:
            out[-1] += f" finally {{"
            self.indent()
            for s in node.finally_body:
                code = self.generate(s)
                if code:
                    out.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
            self.dedent()
            out.append(f"{indent_str}}}")

        if node.else_body:
            self.indent()
            else_lines = [self.generate(s) for s in node.else_body]
            else_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in else_lines if l])
            self.dedent()
            out.append(f"{indent_str}if (_try_ok) {{\n{else_str}\n{indent_str}}}")

        return "\n".join(out)

    def generate_except(self, node: IRExcept) -> str:
        """Generates an except block body."""
        lines = [self.generate(s) for s in node.body]
        return "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in lines])

    def generate_raise(self, node: IRRaise) -> str:
        """Generates a JavaScript throw statement."""
        if node.exception:
            exc_code = self.generate(node.exception)
            if exc_code.startswith("new "):
                return f"throw {exc_code};"
            elif "(" in exc_code:
                return f"throw new {exc_code};"
            else:
                return f"throw new Error({exc_code});"
        return "throw new Error();"

    def generate_binary_operation(self, node: IRBinaryOperation) -> str:
        """Generates a binary operation with mapped JavaScript operators (including 'is', 'is not', 'in' / 'not in')."""
        if node.operator == "is":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in ("null", "None", "undefined") or (isinstance(node.right, IRConstant) and node.right.value is None):
                return f"({left_str} === null || {left_str} === undefined)"
            if left_str in ("null", "None", "undefined") or (isinstance(node.left, IRConstant) and node.left.value is None):
                return f"({right_str} === null || {right_str} === undefined)"
            return f"({left_str} === {right_str})"

        if node.operator == "is not":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in ("null", "None", "undefined") or (isinstance(node.right, IRConstant) and node.right.value is None):
                return f"({left_str} !== null && {left_str} !== undefined)"
            if left_str in ("null", "None", "undefined") or (isinstance(node.left, IRConstant) and node.left.value is None):
                return f"({right_str} !== null && {right_str} !== undefined)"
            return f"({left_str} !== {right_str})"

        if node.operator == "in":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            return f"({right_str}?.has ? {right_str}.has({left_str}) : ({right_str}?.includes ? {right_str}.includes({left_str}) : ({left_str} in {right_str})))"

        if node.operator == "not in":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            return f"!({right_str}?.has ? {right_str}.has({left_str}) : ({right_str}?.includes ? {right_str}.includes({left_str}) : ({left_str} in {right_str})))"

        if node.operator == "//":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            return f"Math.floor({left_str} / {right_str})"

        left_str = self.generate(node.left)
        op_str = JS_OPERATOR_MAP.get(node.operator, node.operator)
        right_str = self.generate(node.right)
        return f"{left_str} {op_str} {right_str}"

    def generate_chained_comparison(self, node: IRChainedComparison) -> str:
        """Generates a chained comparison expression (e.g. 1 < x < 10 -> (1 < x) && (x < 10))."""
        comparisons = []
        for i in range(len(node.operators)):
            left = self.generate(node.operands[i])
            op = JS_OPERATOR_MAP.get(node.operators[i], node.operators[i])
            right = self.generate(node.operands[i + 1])
            comparisons.append(f"({left} {op} {right})")
        return " && ".join(comparisons)

    def generate_lambda(self, node: IRLambda) -> str:
        """Generates a JavaScript arrow function."""
        params_str = ", ".join([self._sanitize_name(p) for p in node.parameters])
        param_hdr = node.parameters[0] if len(node.parameters) == 1 else f"({params_str})"
        body_str = self.generate(node.body)
        return f"({param_hdr} => {body_str})"

    def generate_unary_operation(self, node: IRUnaryOperation) -> str:
        """Generates a unary operation (e.g. !flag, -x)."""
        op_str = JS_OPERATOR_MAP.get(node.operator, node.operator)
        operand_str = self.generate(node.operand)
        return f"{op_str}{operand_str}"

    def generate_function_call(self, node: IRFunctionCall) -> str:
        """
        Generates a function call.
        Maps Python built-ins, reduction operations, and standard libraries to JavaScript APIs.
        """
        if node.name == "sum" and len(node.arguments) == 1 and isinstance(node.arguments[0], IRGeneratorExpression):
            gen = node.arguments[0]
            var = self._sanitize_name(gen.variable.strip(" ()"))
            elt = self.generate(gen.element)
            iter_c = self.generate(gen.iterable)
            if gen.condition:
                cond_c = self.generate(gen.condition)
                return f"{iter_c}.filter({var} => {cond_c}).reduce((_acc, {var}) => _acc + ({elt}), 0)"
            return f"{iter_c}.reduce((_acc, {var}) => _acc + ({elt}), 0)"

        if node.name == "any" and len(node.arguments) == 1 and isinstance(node.arguments[0], IRGeneratorExpression):
            gen = node.arguments[0]
            var = self._sanitize_name(gen.variable.strip(" ()"))
            elt = self.generate(gen.element)
            iter_c = self.generate(gen.iterable)
            return f"{iter_c}.some({var} => {elt})"

        if node.name == "all" and len(node.arguments) == 1 and isinstance(node.arguments[0], IRGeneratorExpression):
            gen = node.arguments[0]
            var = self._sanitize_name(gen.variable.strip(" ()"))
            elt = self.generate(gen.element)
            iter_c = self.generate(gen.iterable)
            return f"{iter_c}.every({var} => {elt})"

        args_list = [self.generate(arg) for arg in node.arguments]
        if node.keywords:
            args_list.extend([self.generate(v) for v in node.keywords.values()])
        args_str = ", ".join(args_list)

        if node.name == "print":
            return f"console.log({args_str})"

        if node.name == "len" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"{arg_str}.length"

        if node.name == "abs" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"Math.abs({arg_str})"

        if node.name == "map" and len(node.arguments) == 2:
            fn_str = self.generate(node.arguments[0])
            iter_str = self.generate(node.arguments[1])
            return f"{iter_str}.map({fn_str})"

        if node.name == "filter" and len(node.arguments) == 2:
            fn_str = self.generate(node.arguments[0])
            iter_str = self.generate(node.arguments[1])
            return f"{iter_str}.filter({fn_str})"

        math_resolved = ModuleMappingRegistry.resolve_math_call("javascript", node.name, args_str)
        if math_resolved:
            code, _ = math_resolved
            return code

        builtin_resolved = ModuleMappingRegistry.resolve_builtin_call("javascript", node.name, args_list)
        if builtin_resolved:
            code, _ = builtin_resolved
            return code

        if node.name == "sorted" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"[...{arg_str}].sort((a, b) => (typeof a === 'number' ? a - b : String(a).localeCompare(String(b))))"

        if node.name == "reversed" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"[...{arg_str}].reverse()"

        if node.name == "min" and len(node.arguments) >= 2:
            return f"Math.min({args_str})"

        if node.name == "max" and len(node.arguments) >= 2:
            return f"Math.max({args_str})"

        if node.name == "str" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"String({arg_str})"

        if node.name == "int" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"parseInt({arg_str}, 10)"

        if node.name == "float" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"parseFloat({arg_str})"

        if node.name == "bool" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"Boolean({arg_str})"

        if "." in node.name:
            obj_name, method_name = node.name.rsplit(".", 1)
            if obj_name == "self":
                obj_name = "this"
            else:
                obj_name = self._sanitize_name(obj_name)

            if method_name == "append" and len(node.arguments) == 1:
                return f"{obj_name}.push({self.generate(node.arguments[0])})"
            elif method_name == "add" and len(node.arguments) == 1:
                return f"{obj_name}.add({self.generate(node.arguments[0])})"
            elif method_name == "pop" and not node.arguments:
                return f"{obj_name}.pop()"
            elif method_name == "remove" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"({obj_name} instanceof Set ? {obj_name}.delete({arg_val}) : {obj_name}.splice({obj_name}.indexOf({arg_val}), 1))"
            elif method_name == "discard" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"({obj_name} instanceof Set ? {obj_name}.delete({arg_val}) : {obj_name}.splice({obj_name}.indexOf({arg_val}), 1))"
            elif method_name == "union" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"new Set([...{obj_name}, ...{arg_val}])"
            elif method_name == "intersection" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"new Set([...{obj_name}].filter(x => {arg_val}.has ? {arg_val}.has(x) : {arg_val}.includes(x)))"
            elif method_name == "difference" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"new Set([...{obj_name}].filter(x => !({arg_val}.has ? {arg_val}.has(x) : {arg_val}.includes(x))))"
            elif method_name == "extend" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"{obj_name}.push(...{arg_val})"
            elif method_name == "insert" and len(node.arguments) == 2:
                idx = self.generate(node.arguments[0])
                el = self.generate(node.arguments[1])
                return f"{obj_name}.splice({idx}, 0, {el})"
            elif method_name == "index" and len(node.arguments) == 1:
                return f"{obj_name}.indexOf({self.generate(node.arguments[0])})"
            elif method_name == "reverse" and not node.arguments:
                return f"{obj_name}.reverse()"
            elif method_name == "sort" and not node.arguments:
                return f"{obj_name}.sort((a, b) => (typeof a === 'number' ? a - b : String(a).localeCompare(String(b))))"
            elif method_name == "count" and len(node.arguments) == 1:
                el = self.generate(node.arguments[0])
                return f"{obj_name}.filter(x => x === {el}).length"

            elif method_name == "upper" and not node.arguments:
                return f"{obj_name}.toUpperCase()"
            elif method_name == "lower" and not node.arguments:
                return f"{obj_name}.toLowerCase()"
            elif method_name == "strip" and not node.arguments:
                return f"{obj_name}.trim()"
            elif method_name == "lstrip" and not node.arguments:
                return f"{obj_name}.trimStart()"
            elif method_name == "rstrip" and not node.arguments:
                return f"{obj_name}.trimEnd()"
            elif method_name == "startswith" and len(node.arguments) == 1:
                return f"{obj_name}.startsWith({self.generate(node.arguments[0])})"
            elif method_name == "endswith" and len(node.arguments) == 1:
                return f"{obj_name}.endsWith({self.generate(node.arguments[0])})"
            elif method_name == "replace" and len(node.arguments) == 2:
                return f"{obj_name}.replaceAll({self.generate(node.arguments[0])}, {self.generate(node.arguments[1])})"
            elif method_name == "split" and len(node.arguments) == 1:
                return f"{obj_name}.split({self.generate(node.arguments[0])})"
            elif method_name == "join" and len(node.arguments) == 1:
                return f"{self.generate(node.arguments[0])}.join({obj_name})"
            elif method_name == "find" and len(node.arguments) == 1:
                return f"{obj_name}.indexOf({self.generate(node.arguments[0])})"

            elif method_name == "get":
                k = self.generate(node.arguments[0])
                d = self.generate(node.arguments[1]) if len(node.arguments) == 2 else "null"
                return f"({obj_name}.hasOwnProperty({k}) ? {obj_name}[{k}] : {d})"
            elif method_name == "setdefault" and len(node.arguments) >= 2:
                k = self.generate(node.arguments[0])
                v = self.generate(node.arguments[1])
                return f"({obj_name}.hasOwnProperty({k}) ? {obj_name}[{k}] : ({obj_name}[{k}] = {v}))"
            elif method_name == "keys" and not node.arguments:
                return f"Object.keys({obj_name})"
            elif method_name == "values" and not node.arguments:
                return f"Object.values({obj_name})"
            elif method_name == "items" and not node.arguments:
                return f"Object.entries({obj_name})"

        if node.name in self._known_classes or (
            node.name and node.name[0].isupper()
            and node.name not in ("Math", "Object", "Array", "Set", "Map", "String", "Number", "Boolean", "JSON", "Error")
        ):
            return f"new {node.name}({args_str})"

        func_name = self._sanitize_name(node.name)
        return f"{func_name}({args_str})"

    def generate_subscript(self, node: IRSubscript) -> str:
        """Generates JavaScript array/object indexing or slicing."""
        val_str = self.generate(node.value)
        if isinstance(node.slice, IRSlice):
            lower = self.generate(node.slice.lower) if node.slice.lower else "0"
            if node.slice.upper:
                upper = self.generate(node.slice.upper)
                return f"{val_str}.slice({lower}, {upper})"
            else:
                return f"{val_str}.slice({lower})"

        idx_str = self.generate(node.slice)
        return f"{val_str}[{idx_str}]"

    def generate_slice(self, node: IRSlice) -> str:
        """Generates a slice string representation."""
        lower = self.generate(node.lower) if node.lower else "0"
        upper = self.generate(node.upper) if node.upper else ""
        return f"{lower}:{upper}"

    def generate_attribute(self, node: IRAttribute) -> str:
        """Generates JavaScript member/property access or math constants."""
        if isinstance(node.value, IRName) and node.value.name == "self":
            return f"this.{self._sanitize_name(node.attribute)}"
        val_str = self.generate(node.value)
        attr = self._sanitize_name(node.attribute)
        const_resolved = ModuleMappingRegistry.resolve_math_constant("javascript", f"{val_str}.{node.attribute}")
        if const_resolved:
            code, _ = const_resolved
            return code
        return f"{val_str}.{attr}"

    def generate_list_comprehension(self, node: IRListComprehension) -> str:
        """Generates code for list comprehension."""
        return "[]"

    def generate_set_comprehension(self, node: IRSetComprehension) -> str:
        """Generates code for set comprehension."""
        return "new Set()"

    def generate_dict_comprehension(self, node: IRDictComprehension) -> str:
        """Generates code for dict comprehension."""
        return "{}"

    def generate_list(self, node: IRList) -> str:
        """Generates a native JavaScript array literal [elem1, elem2]."""
        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"[{elements_str}]"

    def generate_tuple(self, node: IRTuple) -> str:
        """Generates a native JavaScript array literal for tuples [elem1, elem2]."""
        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"[{elements_str}]"

    def generate_set(self, node: IRSet) -> str:
        """Generates a native JavaScript Set literal new Set([...])."""
        if not node.elements:
            return "new Set()"
        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"new Set([{elements_str}])"

    def generate_dict(self, node: IRDict) -> str:
        """Generates a native JavaScript object literal {key: value}."""
        if not node.keys:
            return "{}"

        entries = []
        for k, v in zip(node.keys, node.values):
            key_str = self.generate(k)
            val_str = self.generate(v)
            entries.append(f"{key_str}: {val_str}")
        return f"{{{', '.join(entries)}}}"
