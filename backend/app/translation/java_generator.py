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


JAVA_TYPE_MAP: Dict[str, str] = {
    "int": "int",
    "integer": "int",
    "float": "double",
    "double": "double",
    "str": "String",
    "string": "String",
    "String": "String",
    "bool": "boolean",
    "boolean": "boolean",
    "None": "void",
    "none": "void",
    "void": "void",
    "list": "List<Object>",
    "List": "List<Object>",
    "dict": "Map<Object, Object>",
    "Dict": "Map<Object, Object>",
    "Any": "Object",
    "object": "Object",
    "Object": "Object",
}

JAVA_OPERATOR_MAP: Dict[str, str] = {
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "//": "/",
    "%": "%",
    "==": "==",
    "!=": "!=",
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
}


class JavaGenerator(BaseCodeGenerator):
    """
    Hardened Java target-language code generator.
    Converts IR nodes into fully compilable Java source code with
    type inference, scope tracking, collection support, and import management.
    """

    def __init__(self, indent_size: int = 4, default_class_name: str = "Main"):
        super().__init__(indent_size=indent_size)
        self.default_class_name = default_class_name
        self._required_imports: Set[str] = set()
        self._scope_variables: Dict[str, str] = {}
        self._declared_in_scope: Set[str] = set()
        self._known_classes: Set[str] = set()
        self._current_class: Optional[str] = None

    def reset_state(self) -> None:
        """Resets generator internal scope and import tracking state."""
        self._required_imports.clear()
        self._scope_variables.clear()
        self._declared_in_scope.clear()
        self._known_classes.clear()
        self._current_class = None

    def _resolve_type(self, type_hint: Optional[str], default: str = "Object") -> str:
        """Resolves an IR type hint string to a valid Java type."""
        if not type_hint:
            return default
        return JAVA_TYPE_MAP.get(type_hint.strip(), default)

    def _infer_expression_type(self, node: Optional[IRNode]) -> Optional[str]:
        """
        Infers the Java type of an expression node.
        Returns 'int', 'double', 'String', 'boolean', 'List<Object>', 'Map<Object, Object>', or None.
        """
        if node is None:
            return None

        if isinstance(node, IRConstant):
            if isinstance(node.value, bool):
                return "boolean"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "double"
            elif isinstance(node.value, str):
                return "String"
            elif node.value is None:
                return "Object"

        elif isinstance(node, IRName):
            return self._scope_variables.get(node.name)

        elif isinstance(node, IRBinaryOperation):
            if node.operator in ("==", "!=", "<", "<=", ">", ">=", "and", "or", "&&", "||"):
                return "boolean"
            left_t = self._infer_expression_type(node.left)
            right_t = self._infer_expression_type(node.right)
            if left_t == "double" or right_t == "double":
                return "double"
            if left_t == "String" or right_t == "String":
                return "String"
            if left_t == "int" or right_t == "int":
                return "int"
            return "int"

        elif isinstance(node, IRUnaryOperation):
            if node.operator in ("not", "!"):
                return "boolean"
            return self._infer_expression_type(node.operand) or "int"

        elif isinstance(node, IRList):
            self._required_imports.add("import java.util.List;")
            self._required_imports.add("import java.util.Arrays;")
            return "List<Object>"

        elif isinstance(node, IRDict):
            self._required_imports.add("import java.util.Map;")
            self._required_imports.add("import java.util.HashMap;")
            return "Map<Object, Object>"

        elif isinstance(node, IRSubscript):
            return "Object"

        elif isinstance(node, IRTuple):
            return "List<Object>"

        elif isinstance(node, IRConditionalExpression):
            return self._infer_expression_type(node.then_expression) or "Object"

        elif isinstance(node, IRListComprehension):
            return "List<Object>"

        elif isinstance(node, IRFunctionCall):
            if "." in node.name:
                obj_name, method_name = node.name.rsplit(".", 1)
                if method_name in ("upper", "lower", "strip", "replace"):
                    return "String"
                elif method_name in ("startswith", "endswith"):
                    return "boolean"
                elif method_name in ("index", "count", "find"):
                    return "int"
                elif method_name in ("split", "keys", "values", "items"):
                    return "List<Object>"
                elif method_name in ("append", "extend", "insert", "reverse", "sort"):
                    return "void"
                elif method_name in ("get",):
                    return "Object"

            clean_math = node.name.replace("math.", "")
            if clean_math in ModuleMappingRegistry.MATH_FUNCTIONS:
                return "double"

            if node.name in ("abs", "min", "max"):
                if node.arguments:
                    return self._infer_expression_type(node.arguments[0]) or "int"
                return "int"
            elif node.name in ("int", "len"):
                return "int"
            elif node.name in ("float", "sqrt", "pow", "math.sqrt", "math.pow"):
                return "double"
            elif node.name == "str":
                return "String"
            elif node.name == "bool":
                return "boolean"
            elif node.name in self._known_classes:
                return node.name

        return None

    def generate_program(self, node: IRProgram) -> str:
        """
        Generates code for a complete program.
        Deduplicates imports and wraps standalone functions/statements in a Java class.
        """
        self.reset_state()

        for cls in node.classes:
            self._known_classes.add(cls.name)

        for imp in node.imports:
            imp_code = self.generate(imp)
            if imp_code:
                self._required_imports.add(imp_code)

        if node.classes:
            classes_code = [self.generate(cls) for cls in node.classes]

            top_level_stmts = [
                s for s in node.statements
                if s not in node.functions and s not in node.imports and s not in node.classes
            ]
            full_code = []
            if top_level_stmts:
                main_lines = []
                self.indent()
                self._declared_in_scope.clear()
                self._scope_variables.clear()
                for stmt in top_level_stmts:
                    main_lines.append(f"{self.get_indent()}{self.generate(stmt)}")
                self.dedent()
                main_class = (
                    f"public class Main {{\n"
                    f"{self.get_indent()}public static void main(String[] args) {{\n"
                    + "\n".join(main_lines)
                    + f"\n{self.get_indent()}}}\n}}"
                )
                if self._required_imports:
                    full_code.append("\n".join(sorted(list(self._required_imports))))
                full_code.extend(classes_code)
                full_code.append(main_class)
                return "\n\n".join(full_code).strip()
            else:
                if self._required_imports:
                    full_code.append("\n".join(sorted(list(self._required_imports))))
                full_code.extend(classes_code)
                return "\n\n".join(full_code).strip()

        class_body_lines: List[str] = []
        self.indent()

        for func in node.functions:
            class_body_lines.append(self.generate(func))

        top_level_stmts = [
            s for s in node.statements
            if s not in node.functions and s not in node.imports and s not in node.classes
        ]
        if top_level_stmts:
            main_lines = []
            self.indent()
            self._declared_in_scope.clear()
            self._scope_variables.clear()
            for stmt in top_level_stmts:
                main_lines.append(f"{self.get_indent()}{self.generate(stmt)}")
            self.dedent()
            main_method = (
                f"{self.get_indent()}public static void main(String[] args) {{\n"
                + "\n".join(main_lines)
                + f"\n{self.get_indent()}}}"
            )
            class_body_lines.append(main_method)

        self.dedent()

        class_content = "\n\n".join(class_body_lines)
        class_def = f"public class {self.default_class_name} {{\n{class_content}\n}}"

        if self._required_imports:
            sorted_imports = "\n".join(sorted(list(self._required_imports)))
            return sorted_imports + "\n\n" + class_def
        return class_def

    def generate_import(self, node: IRImport) -> str:
        """Generates a deduplicated Java import statement."""
        module = node.module or ".".join(node.names)
        if module == "math" or "math" in node.names:
            return ""
        import_stmt = f"import {module}.*;"
        self._required_imports.add(import_stmt)
        return import_stmt

    def generate_function(self, node: IRFunction) -> str:
        """
        Generates a Java method with type inference on parameters and return type.
        Tracks local scope to prevent duplicate variable redeclarations.
        """
        prev_declared = set(self._declared_in_scope)
        prev_variables = dict(self._scope_variables)
        self._declared_in_scope.clear()
        self._scope_variables.clear()

        param_types = getattr(node, "parameter_types", {}) or {}

        inferred_types: Dict[str, str] = {}
        for param in node.parameters:
            if param in param_types:
                inferred_types[param] = self._resolve_type(param_types[param])
            else:
                inferred_types[param] = self._resolve_type(param_types.get(param), default="Object")

            self._scope_variables[param] = inferred_types[param]
            self._declared_in_scope.add(param)

        ret_type = self._resolve_type(node.return_type, default="Object")

        params_str = ", ".join([
            f"{inferred_types[param]} {param}"
            for param in node.parameters
        ])

        header = f"{self.get_indent()}public static {ret_type} {node.name}({params_str}) {{"

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
        self._scope_variables = prev_variables

        if not body_lines:
            body_str = f"{self.get_indent()}    // Empty body"
        else:
            body_str = "\n".join(body_lines)

        return f"{header}\n{body_str}\n{self.get_indent()}}}"

    def generate_class(self, node: IRClass) -> str:
        """Generates a full Java class definition with constructor and methods."""
        self._current_class = node.name
        extends_clause = f" extends {node.bases[0]}" if node.bases else ""
        header = f"{self.get_indent()}public class {node.name}{extends_clause} {{"

        self.indent()

        fields: Dict[str, str] = {}
        for stmt in node.body:
            if isinstance(stmt, IRFunction) and stmt.name == "__init__":
                for body_stmt in stmt.body:
                    if isinstance(body_stmt, IRAssignment) and body_stmt.target.startswith("self."):
                        attr_name = body_stmt.target[5:]
                        val_type = self._infer_expression_type(body_stmt.value) or "int"
                        fields[attr_name] = val_type

        field_lines = [f"{self.get_indent()}public {ftype} {fname};" for fname, ftype in fields.items()]

        member_lines: List[str] = []
        for stmt in node.body:
            if isinstance(stmt, IRFunction):
                if stmt.name == "__init__":
                    member_lines.append(self._generate_java_constructor(node.name, stmt))
                else:
                    member_lines.append(self._generate_java_instance_method(stmt))
            else:
                code = self.generate(stmt)
                if code:
                    member_lines.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")

        self.dedent()
        self._current_class = None

        all_body = []
        if field_lines:
            all_body.extend(field_lines)
        if member_lines:
            all_body.extend(member_lines)

        body_str = "\n\n".join(all_body) if all_body else f"{self.get_indent()}    // Empty class"
        return f"{header}\n{body_str}\n{self.get_indent()}}}"

    def _generate_java_constructor(self, class_name: str, node: IRFunction) -> str:
        """Generates a Java constructor from __init__."""
        prev_declared = set(self._declared_in_scope)
        prev_variables = dict(self._scope_variables)
        self._declared_in_scope.clear()
        self._scope_variables.clear()

        params = [p for p in node.parameters if p != "self"]
        param_types = getattr(node, "parameter_types", {}) or {}
        inferred_params = []
        for p in params:
            ptype = self._resolve_type(param_types.get(p), default="int")
            self._scope_variables[p] = ptype
            self._declared_in_scope.add(p)
            inferred_params.append(f"{ptype} {p}")

        header = f"{self.get_indent()}public {class_name}({', '.join(inferred_params)}) {{"
        self.indent()
        body_lines = []
        for stmt in node.body:
            stmt_code = self.generate(stmt)
            if stmt_code:
                if not stmt_code.startswith(" "):
                    stmt_code = f"{self.get_indent()}{stmt_code}"
                body_lines.append(stmt_code)
        self.dedent()

        self._declared_in_scope = prev_declared
        self._scope_variables = prev_variables

        body_str = "\n".join(body_lines) if body_lines else f"{self.get_indent()}    // Empty constructor"
        return f"{header}\n{body_str}\n{self.get_indent()}}}"

    def _generate_java_instance_method(self, node: IRFunction) -> str:
        """Generates a non-static Java instance method."""
        prev_declared = set(self._declared_in_scope)
        prev_variables = dict(self._scope_variables)
        self._declared_in_scope.clear()
        self._scope_variables.clear()

        params = [p for p in node.parameters if p != "self"]
        param_types = getattr(node, "parameter_types", {}) or {}
        inferred_params = []
        for p in params:
            ptype = self._resolve_type(param_types.get(p), default="int")
            self._scope_variables[p] = ptype
            self._declared_in_scope.add(p)
            inferred_params.append(f"{ptype} {p}")

        has_return_val = any(isinstance(s, IRReturn) and s.value is not None for s in node.body)
        ret_type = self._resolve_type(node.return_type, default="int" if has_return_val else "void")

        header = f"{self.get_indent()}public {ret_type} {node.name}({', '.join(inferred_params)}) {{"
        self.indent()
        body_lines = []
        for stmt in node.body:
            stmt_code = self.generate(stmt)
            if stmt_code:
                if not stmt_code.startswith(" "):
                    stmt_code = f"{self.get_indent()}{stmt_code}"
                body_lines.append(stmt_code)
        self.dedent()

        self._declared_in_scope = prev_declared
        self._scope_variables = prev_variables

        body_str = "\n".join(body_lines) if body_lines else f"{self.get_indent()}    // Empty body"
        return f"{header}\n{body_str}\n{self.get_indent()}}}"

    def generate_variable(self, node: IRVariable) -> str:
        """Generates a variable reference or typed declaration."""
        if node.var_type:
            jtype = self._resolve_type(node.var_type)
            return f"{jtype} {node.name}"
        return node.name

    def generate_constant(self, node: IRConstant) -> str:
        """Generates a Java literal constant."""
        if node.value is None:
            return "null"
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, str):
            escaped = node.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'"{escaped}"'
        if isinstance(node.value, float):
            return str(node.value)
        return str(node.value)

    def generate_name(self, node: IRName) -> str:
        """Generates an identifier reference."""
        return node.name

    def generate_assignment(self, node: IRAssignment) -> str:
        """
        Generates a variable assignment statement.
        Infers local variable type on initial declaration and avoids duplicate type declarations.
        """
        var_name = node.target

        if var_name.startswith("self."):
            attr = var_name[5:]
            val_str = self.generate(node.value) if node.value else "null"
            return f"this.{attr} = {val_str};"

        if isinstance(node.value, IRListComprehension):
            comp = node.value
            self._required_imports.add("import java.util.List;")
            self._required_imports.add("import java.util.ArrayList;")
            elem_type = self._infer_expression_type(comp.element) or "Integer"
            if elem_type == "int":
                elem_type = "Integer"
            elif elem_type == "double":
                elem_type = "Double"

            target_name = node.target
            var_name_inner = comp.variable
            elt_code = self.generate(comp.element)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                loop = f"for (int {var_name_inner} = 0; {var_name_inner} < {limit}; {var_name_inner}++) {{\n{self.get_indent()}    {cond_check}{target_name}.add({elt_code});\n{self.get_indent()}}}"
            else:
                iter_code = self.generate(comp.iterable)
                loop = f"for (var {var_name_inner} : {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}.add({elt_code});\n{self.get_indent()}}}"

            decl = f"List<{elem_type}> {target_name} = new ArrayList<>();\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        if isinstance(node.value, IRSetComprehension):
            comp = node.value
            self._required_imports.add("import java.util.Set;")
            self._required_imports.add("import java.util.HashSet;")
            elem_type = self._infer_expression_type(comp.element) or "Integer"
            if elem_type == "int":
                elem_type = "Integer"
            elif elem_type == "double":
                elem_type = "Double"

            target_name = node.target
            var_name_inner = comp.variable
            elt_code = self.generate(comp.element)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                loop = f"for (int {var_name_inner} = 0; {var_name_inner} < {limit}; {var_name_inner}++) {{\n{self.get_indent()}    {cond_check}{target_name}.add({elt_code});\n{self.get_indent()}}}"
            else:
                iter_code = self.generate(comp.iterable)
                loop = f"for (var {var_name_inner} : {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}.add({elt_code});\n{self.get_indent()}}}"

            decl = f"Set<{elem_type}> {target_name} = new HashSet<>();\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        if isinstance(node.value, IRDictComprehension):
            comp = node.value
            self._required_imports.add("import java.util.Map;")
            self._required_imports.add("import java.util.HashMap;")
            k_type = self._infer_expression_type(comp.key)
            if not k_type and isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                k_type = "Integer"
            k_type = k_type or "String"
            v_type = self._infer_expression_type(comp.value)
            if not v_type and isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                v_type = "Integer"
            v_type = v_type or "Integer"
            if k_type == "int":
                k_type = "Integer"
            if v_type == "int":
                v_type = "Integer"

            target_name = node.target
            k_code = self.generate(comp.key)
            v_code = self.generate(comp.value)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                var_name_inner = comp.variable.strip(" ()")
                loop = f"for (int {var_name_inner} = 0; {var_name_inner} < {limit}; {var_name_inner}++) {{\n{self.get_indent()}    {cond_check}{target_name}.put({k_code}, {v_code});\n{self.get_indent()}}}"
            elif "," in comp.variable:
                k_var, v_var = [v.strip(" ()") for v in comp.variable.split(",")]
                iter_code = self.generate(comp.iterable)
                loop = f"for (var entry : {iter_code}) {{\n{self.get_indent()}    var {k_var} = entry.getKey();\n{self.get_indent()}    var {v_var} = entry.getValue();\n{self.get_indent()}    {cond_check}{target_name}.put({k_code}, {v_code});\n{self.get_indent()}}}"
            else:
                var_name_inner = comp.variable.strip(" ()")
                iter_code = self.generate(comp.iterable)
                loop = f"for (var {var_name_inner} : {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}.put({k_code}, {v_code});\n{self.get_indent()}}}"

            decl = f"Map<{k_type}, {v_type}> {target_name} = new HashMap<>();\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        val_str = self.generate(node.value) if node.value else "null"

        if node.var_type:
            jtype = self._resolve_type(node.var_type)
            self._scope_variables[var_name] = jtype
            self._declared_in_scope.add(var_name)
            return f"{jtype} {var_name} = {val_str};"

        if var_name in self._declared_in_scope:
            return f"{var_name} = {val_str};"

        inferred_type = self._infer_expression_type(node.value)
        if inferred_type:
            self._scope_variables[var_name] = inferred_type
            self._declared_in_scope.add(var_name)
            return f"{inferred_type} {var_name} = {val_str};"

        return f"{var_name} = {val_str};"

    def generate_tuple_assignment(self, node: IRTupleAssignment) -> str:
        """Generates multiple assignment / tuple unpacking in Java."""
        if isinstance(node.value, (IRTuple, IRList)):
            lines = []
            for target, val_node in zip(node.targets, node.value.elements):
                lines.append(self.generate_assignment(IRAssignment(target=target, value=val_node)))
            return "\n".join(lines)
        else:
            val_str = self.generate(node.value)
            lines = []
            for i, target in enumerate(node.targets):
                if target not in self._declared_in_scope:
                    self._declared_in_scope.add(target)
                    lines.append(f"var {target} = {val_str}.get({i});")
                else:
                    lines.append(f"{target} = {val_str}.get({i});")
            return f"\n{self.get_indent()}".join(lines)

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
        """Generates a Java for loop (handles range(), enumerate(), zip(), enhanced for-each, and loop else)."""
        indent_str = self.get_indent()
        break_flag = "_completed" if node.else_body else None

        if "," in node.variable and isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "enumerate":
            targets = [v.strip(" ()") for v in node.variable.split(",")]
            idx_var, val_var = targets[0], targets[1]
            coll_str = self.generate(node.iterable.arguments[0])
            loop_header = f"for (int {idx_var} = 0; {idx_var} < {coll_str}.size(); {idx_var}++)"
            self.indent()
            body_lines = [f"var {val_var} = {coll_str}.get({idx_var});"]
            self._declared_in_scope.add(idx_var)
            self._declared_in_scope.add(val_var)
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code)
            body_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        elif "," in node.variable and isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "zip":
            targets = [v.strip(" ()") for v in node.variable.split(",")]
            var_a, var_b = targets[0], targets[1]
            xs_str = self.generate(node.iterable.arguments[0])
            ys_str = self.generate(node.iterable.arguments[1])
            idx_var = "_zip_idx"
            loop_header = f"for (int {idx_var} = 0; {idx_var} < Math.min({xs_str}.size(), {ys_str}.size()); {idx_var}++)"
            self.indent()
            body_lines = [
                f"var {var_a} = {xs_str}.get({idx_var});",
                f"var {var_b} = {ys_str}.get({idx_var});",
            ]
            self._declared_in_scope.add(var_a)
            self._declared_in_scope.add(var_b)
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code)
            body_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        elif "," in node.variable:
            targets = [v.strip(" ()") for v in node.variable.split(",")]
            k_var, v_var = targets[0], targets[1]
            iter_str = self.generate(node.iterable)
            if iter_str.endswith(".entrySet()"):
                loop_header = f"for (var entry : {iter_str})"
            elif iter_str.endswith(".items()"):
                clean_iter = iter_str[:-8]
                loop_header = f"for (var entry : {clean_iter}.entrySet())"
            else:
                loop_header = f"for (var entry : {iter_str}.entrySet())"
            self.indent()
            body_lines = [
                f"var {k_var} = entry.getKey();",
                f"var {v_var} = entry.getValue();",
            ]
            self._declared_in_scope.add(k_var)
            self._declared_in_scope.add(v_var)
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code)
            body_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        elif isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "range":
            args = node.iterable.arguments
            if len(args) == 1:
                start_val = "0"
                stop_val = self.generate(args[0])
                loop_header = f"for (int {node.variable} = {start_val}; {node.variable} < {stop_val}; {node.variable}++)"
            elif len(args) == 2:
                start_val = self.generate(args[0])
                stop_val = self.generate(args[1])
                loop_header = f"for (int {node.variable} = {start_val}; {node.variable} < {stop_val}; {node.variable}++)"
            elif len(args) >= 3:
                start_val = self.generate(args[0])
                stop_val = self.generate(args[1])
                step_val = self.generate(args[2])
                if step_val.strip().startswith("-"):
                    loop_header = f"for (int {node.variable} = {start_val}; {node.variable} > {stop_val}; {node.variable} += {step_val})"
                else:
                    loop_header = f"for (int {node.variable} = {start_val}; {node.variable} < {stop_val}; {node.variable} += {step_val})"
            else:
                start_val = "0"
                stop_val = "0"
                loop_header = f"for (int {node.variable} = {start_val}; {node.variable} < {stop_val}; {node.variable}++)"
            self._scope_variables[node.variable] = "int"
            self._declared_in_scope.add(node.variable)
            self.indent()
            body_lines = []
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code)
            body_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"
        else:
            iter_str = self.generate(node.iterable)
            loop_header = f"for (Object {node.variable} : {iter_str})"
            self._scope_variables[node.variable] = "Object"
            self._declared_in_scope.add(node.variable)
            self.indent()
            body_lines = []
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code)
            body_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l])
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        if node.else_body:
            self.indent()
            else_lines = [self.generate(s) for s in node.else_body]
            else_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in else_lines if l])
            self.dedent()
            return f"{indent_str}boolean _completed = true;\n{loop_code}\n{indent_str}if (_completed) {{\n{else_str}\n{indent_str}}}"

        return loop_code

    def generate_while(self, node: IRWhile) -> str:
        """Generates a Java while loop (including while/else lowering)."""
        indent_str = self.get_indent()
        cond_str = self.generate(node.condition)
        break_flag = "_completed" if node.else_body else None

        self.indent()
        body_lines = []
        for s in node.body:
            code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
            if code:
                body_lines.append(code)
        body_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in body_lines if l])
        self.dedent()

        loop_code = f"{indent_str}while ({cond_str}) {{\n{body_str}\n{indent_str}}}"

        if node.else_body:
            self.indent()
            else_lines = [self.generate(s) for s in node.else_body]
            else_str = "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in else_lines if l])
            self.dedent()
            return f"{indent_str}boolean _completed = true;\n{loop_code}\n{indent_str}if (_completed) {{\n{else_str}\n{indent_str}}}"

        return loop_code

    def generate_break(self, node: IRBreak) -> str:
        """Generates a Java break statement."""
        return "break;"

    def generate_continue(self, node: IRContinue) -> str:
        """Generates a Java continue statement."""
        return "continue;"

    def generate_assert(self, node: IRAssert) -> str:
        """Generates a Java assertion statement."""
        indent_str = self.get_indent()
        cond_str = self.generate(node.condition)
        if node.message:
            msg_str = self.generate(node.message)
            return f"{indent_str}if (!({cond_str})) throw new AssertionError({msg_str});"
        return f"{indent_str}if (!({cond_str})) throw new AssertionError(\"Assertion failed\");"

    def generate_yield(self, node: IRYield) -> str:
        """Generates code for a yield statement/expression in Java."""
        val_str = self.generate(node.value) if node.value else "null"
        return f"/* yield */ {val_str};"

    def generate_generator_expression(self, node: IRGeneratorExpression) -> str:
        """Generates Java Stream pipeline from generator expression."""
        var_name = node.variable.strip(" ()")
        elt_str = self.generate(node.element)
        iter_str = self.generate(node.iterable)
        if node.condition:
            cond_str = self.generate(node.condition)
            return f"{iter_str}.stream().filter({var_name} -> {cond_str}).map({var_name} -> {elt_str})"
        return f"{iter_str}.stream().map({var_name} -> {elt_str})"

    def generate_starred(self, node: IRStarred) -> str:
        """Generates code for a starred argument (*args or **kwargs)."""
        return self.generate(node.value)

    def generate_isinstance(self, node: IRIsInstance) -> str:
        """Generates a Java instanceof expression."""
        expr_str = self.generate(node.expression)
        type_map = {
            "int": "Integer",
            "str": "String",
            "float": "Double",
            "bool": "Boolean",
            "list": "List",
            "dict": "Map",
            "set": "Set",
        }
        j_type = type_map.get(node.type_name, node.type_name)
        return f"({expr_str} instanceof {j_type})"

    def generate_try(self, node: IRTry) -> str:
        """Generates a Java try-catch-finally block (including multiple handlers and try/else)."""
        indent_str = self.get_indent()
        out = []

        if node.else_body:
            out.append(f"{indent_str}boolean _try_ok = true;")

        out.append(f"{indent_str}try {{")
        self.indent()
        for s in node.body:
            code = self.generate(s)
            if code:
                out.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
        self.dedent()
        out.append(f"{indent_str}}}")

        exc_map = {
            "ValueError": "IllegalArgumentException",
            "TypeError": "ClassCastException",
            "IndexError": "IndexOutOfBoundsException",
            "KeyError": "java.util.NoSuchElementException",
            "ZeroDivisionError": "ArithmeticException",
            "Exception": "Exception",
            "BaseException": "Exception",
        }

        for i, h in enumerate(node.handlers):
            exc_type = exc_map.get(h.exception_type, h.exception_type) if h.exception_type else "Exception"
            alias = h.alias or ("e" if len(node.handlers) == 1 else f"e_{i}")
            out[-1] += f" catch ({exc_type} {alias}) {{"
            self.indent()
            if node.else_body:
                out.append(f"{self.get_indent()}_try_ok = false;")
            for s in h.body:
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

        if node.finally_body:
            out[-1] += f" finally {{"
            self.indent()
            for s in node.finally_body:
                code = self.generate(s)
                if code:
                    out.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
            self.dedent()
            out.append(f"{indent_str}}}")

        return "\n".join(out)

    def generate_except(self, node: IRExcept) -> str:
        """Generates an except block body (used in try-catch)."""
        lines = [self.generate(s) for s in node.body]
        return "\n".join([l if l.startswith(" ") else f"{self.get_indent()}{l}" for l in lines])

    def generate_raise(self, node: IRRaise) -> str:
        """Generates a Java throw statement."""
        if node.exception:
            exc_code = self.generate(node.exception)
            if exc_code.startswith("new "):
                return f"throw {exc_code};"
            elif "(" in exc_code:
                return f"throw new {exc_code};"
            else:
                return f"throw new RuntimeException({exc_code});"
        return "throw new RuntimeException();"

    def generate_binary_operation(self, node: IRBinaryOperation) -> str:
        """
        Generates a binary operation with mapped Java operators.
        Handles arithmetic, comparison, identity ('is', 'is not'), and membership ('in', 'not in').
        """
        if node.operator == "is":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in ("null", "None") or (isinstance(node.right, IRConstant) and node.right.value is None):
                return f"({left_str} == null)"
            if left_str in ("null", "None") or (isinstance(node.left, IRConstant) and node.left.value is None):
                return f"({right_str} == null)"
            return f"({left_str} == {right_str})"

        if node.operator == "is not":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in ("null", "None") or (isinstance(node.right, IRConstant) and node.right.value is None):
                return f"({left_str} != null)"
            if left_str in ("null", "None") or (isinstance(node.left, IRConstant) and node.left.value is None):
                return f"({right_str} != null)"
            return f"({left_str} != {right_str})"

        if node.operator == "in":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if "keySet" in right_str or right_str.endswith(".keySet()"):
                return f"{right_str}.contains({left_str})"
            elif "." in right_str and ("Map" in right_str or "dict" in right_str.lower() or "data" in right_str.lower()):
                return f"({right_str}.containsKey({left_str}))"
            else:
                return f"{right_str}.contains({left_str})"

        if node.operator == "not in":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if "keySet" in right_str or right_str.endswith(".keySet()"):
                return f"!{right_str}.contains({left_str})"
            elif "." in right_str and ("Map" in right_str or "dict" in right_str.lower() or "data" in right_str.lower()):
                return f"(!{right_str}.containsKey({left_str}))"
            else:
                return f"!{right_str}.contains({left_str})"

        left_type = getattr(node.left, "var_type", None) or (
            self._scope_variables.get(node.left.name) if isinstance(node.left, IRName) and getattr(node.left, "is_explicit_object", False) else None
        )
        right_type = getattr(node.right, "var_type", None) or (
            self._scope_variables.get(node.right.name) if isinstance(node.right, IRName) and getattr(node.right, "is_explicit_object", False) else None
        )

        if (left_type == "Object" or right_type == "Object") and node.operator in ("-", "*", "/", "%", ">", "<", ">=", "<="):
            raise TranslationError(
                f"Invalid Java operation: operator '{node.operator}' cannot be applied to type 'Object'. "
                f"Explicit primitive type annotations (e.g. 'int' or 'double') are required."
            )

        left_str = self.generate(node.left)
        op_str = JAVA_OPERATOR_MAP.get(node.operator, node.operator)
        right_str = self.generate(node.right)
        return f"{left_str} {op_str} {right_str}"

    def generate_chained_comparison(self, node: IRChainedComparison) -> str:
        """Generates a chained comparison expression (e.g. 1 < x < 10 -> (1 < x) && (x < 10))."""
        comparisons = []
        for i in range(len(node.operators)):
            left = self.generate(node.operands[i])
            op = JAVA_OPERATOR_MAP.get(node.operators[i], node.operators[i])
            right = self.generate(node.operands[i + 1])
            comparisons.append(f"({left} {op} {right})")
        return " && ".join(comparisons)

    def generate_lambda(self, node: IRLambda) -> str:
        """Generates a Java lambda expression."""
        params_str = ", ".join(node.parameters)
        param_hdr = node.parameters[0] if len(node.parameters) == 1 else f"({params_str})"
        body_str = self.generate(node.body)
        return f"({param_hdr} -> {body_str})"

    def generate_unary_operation(self, node: IRUnaryOperation) -> str:
        """Generates a unary operation (e.g. !flag, -x)."""
        op_str = JAVA_OPERATOR_MAP.get(node.operator, node.operator)
        operand_str = self.generate(node.operand)
        return f"{op_str}{operand_str}"

    def generate_function_call(self, node: IRFunctionCall) -> str:
        """
        Generates a function/method call.
        Maps Python built-ins, functional helpers, and collection/string methods to standard Java APIs.
        """
        args_list = [self.generate(arg) for arg in node.arguments]
        if node.keywords:
            args_list.extend([self.generate(v) for v in node.keywords.values()])
        args_str = ", ".join(args_list)

        if node.name == "print":
            return f"System.out.println({args_str})"

        if node.name == "len" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"{arg_str}.size()"

        if node.name == "abs" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"Math.abs({arg_str})"

        if node.name == "map" and len(node.arguments) == 2:
            self._required_imports.add("import java.util.stream.Collectors;")
            fn_str = self.generate(node.arguments[0])
            iter_str = self.generate(node.arguments[1])
            return f"{iter_str}.stream().map({fn_str}).collect(Collectors.toList())"

        if node.name == "filter" and len(node.arguments) == 2:
            self._required_imports.add("import java.util.stream.Collectors;")
            fn_str = self.generate(node.arguments[0])
            iter_str = self.generate(node.arguments[1])
            return f"{iter_str}.stream().filter({fn_str}).collect(Collectors.toList())"

        math_resolved = ModuleMappingRegistry.resolve_math_call("java", node.name, args_str)
        if math_resolved:
            code, _ = math_resolved
            return code

        builtin_resolved = ModuleMappingRegistry.resolve_builtin_call("java", node.name, args_list)
        if builtin_resolved:
            code, _ = builtin_resolved
            return code

        if node.name == "sorted" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            self._required_imports.add("import java.util.Collections;")
            self._required_imports.add("import java.util.ArrayList;")
            return f"new ArrayList<>({arg_str})"

        if node.name == "reversed" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            self._required_imports.add("import java.util.Collections;")
            self._required_imports.add("import java.util.ArrayList;")
            return f"new ArrayList<>({arg_str})"

        if node.name == "min" and len(node.arguments) >= 2:
            args = [self.generate(arg) for arg in node.arguments]
            result = f"Math.min({args[0]}, {args[1]})"
            for next_arg in args[2:]:
                result = f"Math.min({result}, {next_arg})"
            return result

        if node.name == "max" and len(node.arguments) >= 2:
            args = [self.generate(arg) for arg in node.arguments]
            result = f"Math.max({args[0]}, {args[1]})"
            for next_arg in args[2:]:
                result = f"Math.max({result}, {next_arg})"
            return result

        if node.name == "str" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"String.valueOf({arg_str})"

        if node.name == "int" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"(int) ({arg_str})"

        if node.name == "float" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"(double) ({arg_str})"

        if node.name == "bool" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"Boolean.parseBoolean(String.valueOf({arg_str}))"

        if "." in node.name:
            obj_name, method_name = node.name.rsplit(".", 1)
            if obj_name == "self":
                obj_name = "this"

            if method_name == "append" and len(node.arguments) == 1:
                return f"{obj_name}.add({self.generate(node.arguments[0])})"
            elif method_name == "add" and len(node.arguments) == 1:
                return f"{obj_name}.add({self.generate(node.arguments[0])})"
            elif method_name == "pop" and not node.arguments:
                return f"{obj_name}.remove({obj_name}.size() - 1)"
            elif method_name == "remove" and len(node.arguments) == 1:
                return f"{obj_name}.remove({self.generate(node.arguments[0])})"
            elif method_name == "discard" and len(node.arguments) == 1:
                return f"{obj_name}.remove({self.generate(node.arguments[0])})"
            elif method_name == "union" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"([&]{{ var _s = new HashSet<>({obj_name}); _s.addAll({arg_val}); return _s; }}())"
            elif method_name == "intersection" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"([&]{{ var _s = new HashSet<>({obj_name}); _s.retainAll({arg_val}); return _s; }}())"
            elif method_name == "difference" and len(node.arguments) == 1:
                arg_val = self.generate(node.arguments[0])
                return f"([&]{{ var _s = new HashSet<>({obj_name}); _s.removeAll({arg_val}); return _s; }}())"
            elif method_name == "extend" and len(node.arguments) == 1:
                return f"{obj_name}.addAll({self.generate(node.arguments[0])})"
            elif method_name == "insert" and len(node.arguments) == 2:
                idx = self.generate(node.arguments[0])
                el = self.generate(node.arguments[1])
                return f"{obj_name}.add({idx}, {el})"
            elif method_name == "index" and len(node.arguments) == 1:
                return f"{obj_name}.indexOf({self.generate(node.arguments[0])})"
            elif method_name == "reverse" and not node.arguments:
                self._required_imports.add("import java.util.Collections;")
                return f"Collections.reverse({obj_name})"
            elif method_name == "sort" and not node.arguments:
                self._required_imports.add("import java.util.Collections;")
                return f"Collections.sort({obj_name})"
            elif method_name == "count" and len(node.arguments) == 1:
                self._required_imports.add("import java.util.Collections;")
                el = self.generate(node.arguments[0])
                return f"Collections.frequency({obj_name}, {el})"

            elif method_name == "upper" and not node.arguments:
                return f"{obj_name}.toUpperCase()"
            elif method_name == "lower" and not node.arguments:
                return f"{obj_name}.toLowerCase()"
            elif method_name == "strip" and not node.arguments:
                return f"{obj_name}.trim()"
            elif method_name == "lstrip" and not node.arguments:
                return f"{obj_name}.replaceAll(\"^\\\\s+\", \"\")"
            elif method_name == "rstrip" and not node.arguments:
                return f"{obj_name}.replaceAll(\"\\\\s+$\", \"\")"
            elif method_name == "startswith" and len(node.arguments) == 1:
                return f"{obj_name}.startsWith({self.generate(node.arguments[0])})"
            elif method_name == "endswith" and len(node.arguments) == 1:
                return f"{obj_name}.endsWith({self.generate(node.arguments[0])})"
            elif method_name == "replace" and len(node.arguments) == 2:
                return f"{obj_name}.replace({self.generate(node.arguments[0])}, {self.generate(node.arguments[1])})"
            elif method_name == "split" and len(node.arguments) == 1:
                self._required_imports.add("import java.util.Arrays;")
                return f"Arrays.asList({obj_name}.split({self.generate(node.arguments[0])}))"
            elif method_name == "join" and len(node.arguments) == 1:
                return f"String.join({obj_name}, {self.generate(node.arguments[0])})"
            elif method_name == "find" and len(node.arguments) == 1:
                return f"{obj_name}.indexOf({self.generate(node.arguments[0])})"

            elif method_name == "get":
                if len(node.arguments) == 1:
                    return f"{obj_name}.get({self.generate(node.arguments[0])})"
                elif len(node.arguments) == 2:
                    return f"{obj_name}.getOrDefault({self.generate(node.arguments[0])}, {self.generate(node.arguments[1])})"
            elif method_name == "setdefault" and len(node.arguments) >= 2:
                k = self.generate(node.arguments[0])
                v = self.generate(node.arguments[1])
                return f"{obj_name}.putIfAbsent({k}, {v})"
            elif method_name == "keys" and not node.arguments:
                return f"{obj_name}.keySet()"
            elif method_name == "values" and not node.arguments:
                return f"{obj_name}.values()"
            elif method_name == "items" and not node.arguments:
                return f"{obj_name}.entrySet()"

        if node.name in self._known_classes or (
            node.name and node.name[0].isupper()
            and node.name not in ("Math", "Arrays", "List", "Map", "Set", "HashSet", "String", "Boolean", "Integer", "Double", "Object", "System", "Collections")
        ):
            return f"new {node.name}({args_str})"

        return f"{node.name}({args_str})"

    def generate_subscript(self, node: IRSubscript) -> str:
        """Generates Java collection/string indexing or slicing."""
        val_str = self.generate(node.value)
        if isinstance(node.slice, IRSlice):
            lower = self.generate(node.slice.lower) if node.slice.lower else "0"
            if node.slice.upper:
                upper = self.generate(node.slice.upper)
                return f"{val_str}.subList({lower}, {upper})"
            else:
                return f"{val_str}.subList({lower}, {val_str}.size())"

        idx_str = self.generate(node.slice)
        return f"{val_str}.get({idx_str})"

    def generate_slice(self, node: IRSlice) -> str:
        """Generates a slice string representation."""
        lower = self.generate(node.lower) if node.lower else "0"
        upper = self.generate(node.upper) if node.upper else ""
        return f"{lower}:{upper}"

    def generate_attribute(self, node: IRAttribute) -> str:
        """Generates Java member/field access or math constants."""
        if isinstance(node.value, IRName) and node.value.name == "self":
            return f"this.{node.attribute}"
        val_str = self.generate(node.value)
        const_resolved = ModuleMappingRegistry.resolve_math_constant("java", f"{val_str}.{node.attribute}")
        if const_resolved:
            code, _ = const_resolved
            return code
        return f"{val_str}.{node.attribute}"

    def generate_list_comprehension(self, node: IRListComprehension) -> str:
        """Generates code for list comprehension."""
        return "new ArrayList<>()"

    def generate_set_comprehension(self, node: IRSetComprehension) -> str:
        """Generates code for set comprehension."""
        return "new HashSet<>()"

    def generate_dict_comprehension(self, node: IRDictComprehension) -> str:
        """Generates code for dict comprehension."""
        return "new HashMap<>()"

    def generate_list(self, node: IRList) -> str:
        """Generates Java List initialization (Arrays.asList)."""
        self._required_imports.add("import java.util.List;")
        self._required_imports.add("import java.util.Arrays;")

        if not node.elements:
            self._required_imports.add("import java.util.ArrayList;")
            return "new ArrayList<>()"

        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"Arrays.asList({elements_str})"

    def generate_tuple(self, node: IRTuple) -> str:
        """Generates Java List representing a tuple (Arrays.asList)."""
        self._required_imports.add("import java.util.List;")
        self._required_imports.add("import java.util.Arrays;")

        if not node.elements:
            self._required_imports.add("import java.util.ArrayList;")
            return "new ArrayList<>()"

        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"Arrays.asList({elements_str})"

    def generate_set(self, node: IRSet) -> str:
        """Generates Java Set initialization (HashSet)."""
        self._required_imports.add("import java.util.Set;")
        self._required_imports.add("import java.util.HashSet;")
        self._required_imports.add("import java.util.Arrays;")

        if not node.elements:
            return "new HashSet<>()"

        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"new HashSet<>(Arrays.asList({elements_str}))"

    def generate_dict(self, node: IRDict) -> str:
        """Generates Java Map initialization (Map.of or HashMap)."""
        self._required_imports.add("import java.util.Map;")
        self._required_imports.add("import java.util.HashMap;")

        if not node.keys:
            return "new HashMap<>()"

        entries = []
        for k, v in zip(node.keys, node.values):
            entries.append(f"{self.generate(k)}, {self.generate(v)}")
        return f"Map.of({', '.join(entries)})"
