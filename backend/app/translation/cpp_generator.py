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


CPP_TYPE_MAP: Dict[str, str] = {
    "int": "int",
    "integer": "int",
    "float": "double",
    "double": "double",
    "str": "std::string",
    "string": "std::string",
    "std::string": "std::string",
    "bool": "bool",
    "boolean": "bool",
    "None": "void",
    "none": "void",
    "void": "void",
    "list": "std::vector<int>",
    "List": "std::vector<int>",
    "dict": "std::map<std::string, int>",
    "Dict": "std::map<std::string, int>",
    "Any": "auto",
    "object": "auto",
    "Object": "auto",
}

CPP_OPERATOR_MAP: Dict[str, str] = {
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

CPP_KEYWORDS = {
    "alignas", "alignof", "and_eq", "asm", "atomic_cancel", "atomic_commit",
    "atomic_noexcept", "auto", "bitand", "bitor", "bool", "break", "case",
    "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl",
    "concept", "const", "consteval", "constexpr", "constinit", "const_cast",
    "continue", "co_await", "co_return", "co_yield", "decltype", "default",
    "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit",
    "export", "extern", "false", "float", "for", "friend", "goto", "if",
    "inline", "int", "long", "mutable", "namespace", "new", "noexcept",
    "not_eq", "nullptr", "operator", "or_eq", "private", "protected", "public",
    "reflexpr", "register", "reinterpret_cast", "requires", "return", "short",
    "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
    "switch", "synchronized", "template", "this", "thread_local", "throw",
    "true", "try", "typedef", "typeid", "typename", "union", "unsigned",
    "using", "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
}


class CppGenerator(BaseCodeGenerator):
    """
    C++ target-language code generator.
    Converts language-agnostic IR nodes into standard C++ source code with
    type inference, scope tracking, collection support, and include management.
    """

    def __init__(self, indent_size: int = 4):
        super().__init__(indent_size=indent_size)
        self._required_includes: Set[str] = set()
        self._scope_variables: Dict[str, str] = {}
        self._declared_in_scope: Set[str] = set()
        self._known_classes: Set[str] = set()

    def reset_state(self) -> None:
        """Resets generator internal scope and include tracking state."""
        self._required_includes.clear()
        self._scope_variables.clear()
        self._declared_in_scope.clear()
        self._known_classes.clear()

    def _sanitize_name(self, name: str) -> str:
        """
        Appends an underscore if the identifier collides with a C++ reserved keyword.
        """
        if name in CPP_KEYWORDS:
            return f"{name}_"
        return name

    def _resolve_type(self, type_hint: Optional[str], default: str = "int") -> str:
        """
        Resolves an IR type hint string to a valid C++ type and registers required headers.
        """
        if not type_hint:
            return default
        resolved = CPP_TYPE_MAP.get(type_hint.strip(), default)
        if "std::string" in resolved:
            self._required_includes.add("#include <string>")
        elif "std::vector" in resolved:
            self._required_includes.add("#include <vector>")
        elif "std::map" in resolved:
            self._required_includes.add("#include <map>")
        return resolved

    def _infer_expression_type(self, node: Optional[IRNode]) -> Optional[str]:
        """
        Infers the C++ type of an expression node.
        Returns 'int', 'double', 'std::string', 'bool', 'std::vector<...>', 'std::map<...>', or None.
        """
        if node is None:
            return None

        if isinstance(node, IRConstant):
            if isinstance(node.value, bool):
                return "bool"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "double"
            elif isinstance(node.value, str):
                self._required_includes.add("#include <string>")
                return "std::string"
            elif node.value is None:
                return "void*"

        elif isinstance(node, IRName):
            return self._scope_variables.get(node.name)

        elif isinstance(node, IRBinaryOperation):
            if node.operator in ("==", "!=", "<", "<=", ">", ">=", "and", "or", "&&", "||"):
                return "bool"
            left_t = self._infer_expression_type(node.left)
            right_t = self._infer_expression_type(node.right)
            if left_t == "double" or right_t == "double":
                return "double"
            if left_t == "std::string" or right_t == "std::string":
                self._required_includes.add("#include <string>")
                return "std::string"
            if left_t == "int" or right_t == "int":
                return "int"
            return "int"

        elif isinstance(node, IRUnaryOperation):
            if node.operator in ("not", "!"):
                return "bool"
            return self._infer_expression_type(node.operand) or "int"

        elif isinstance(node, IRList):
            self._required_includes.add("#include <vector>")
            elem_type = self._infer_expression_type(node.elements[0]) if node.elements else "int"
            return f"std::vector<{elem_type or 'int'}>"

        elif isinstance(node, IRDict):
            self._required_includes.add("#include <map>")
            k_type = self._infer_expression_type(node.keys[0]) if node.keys else "std::string"
            v_type = self._infer_expression_type(node.values[0]) if node.values else "int"
            return f"std::map<{k_type or 'std::string'}, {v_type or 'int'}>"

        elif isinstance(node, IRTuple):
            self._required_includes.add("#include <tuple>")
            return "auto"

        elif isinstance(node, IRConditionalExpression):
            return self._infer_expression_type(node.then_expression) or "auto"

        elif isinstance(node, IRSubscript):
            return "auto"

        elif isinstance(node, IRListComprehension):
            self._required_includes.add("#include <vector>")
            elem_type = self._infer_expression_type(node.element) or "int"
            return f"std::vector<{elem_type}>"

        elif isinstance(node, IRFunctionCall):
            if "." in node.name:
                obj_name, method_name = node.name.rsplit(".", 1)
                if method_name in ("startswith", "endswith"):
                    return "bool"
                elif method_name in ("index", "count", "find"):
                    return "int"

            clean_math = node.name.replace("math.", "")
            if clean_math in ModuleMappingRegistry.MATH_FUNCTIONS:
                self._required_includes.add("#include <cmath>")
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
                self._required_includes.add("#include <string>")
                return "std::string"
            elif node.name == "bool":
                return "bool"
            elif node.name in self._known_classes:
                return node.name

        return None

    def generate_program(self, node: IRProgram) -> str:
        """
        Generates code for a complete C++ translation unit.
        Deduplicates includes and outputs functions/classes, wrapping
        top-level statements in main() if present.
        """
        self.reset_state()

        for cls in node.classes:
            self._known_classes.add(self._sanitize_name(cls.name))

        for imp in node.imports:
            self.generate(imp)

        content_blocks: List[str] = []

        for cls in node.classes:
            content_blocks.append(self.generate(cls))

        for func in node.functions:
            content_blocks.append(self.generate(func))

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
            main_lines.append(f"{self.get_indent()}return 0;")
            self.dedent()
            main_func = "int main() {\n" + "\n".join(main_lines) + "\n}"
            content_blocks.append(main_func)

        full_code = "\n\n".join(content_blocks).strip()

        if self._required_includes:
            sorted_includes = "\n".join(sorted(list(self._required_includes)))
            if full_code:
                return sorted_includes + "\n\n" + full_code
            return sorted_includes

        return full_code

    def generate_import(self, node: IRImport) -> str:
        """Generates a C++ #include directive."""
        module = node.module or (node.names[0] if node.names else "")
        if not module:
            return ""

        if module == "math" or "math" in node.names:
            inc = "#include <cmath>"
        elif module.startswith("<") or module.startswith('"'):
            inc = f"#include {module}"
        else:
            inc = f"#include <{module}>"

        self._required_includes.add(inc)
        return inc

    def generate_function(self, node: IRFunction) -> str:
        """
        Generates a C++ free function definition.
        Resolves return type and parameter types, and manages parameter scopes.
        """
        prev_declared = set(self._declared_in_scope)
        prev_variables = dict(self._scope_variables)
        self._declared_in_scope.clear()
        self._scope_variables.clear()

        param_types = getattr(node, "parameter_types", {}) or {}

        inferred_params: Dict[str, str] = {}
        for param in node.parameters:
            clean_param = self._sanitize_name(param)
            if param in param_types:
                ptype = self._resolve_type(param_types[param])
            else:
                ptype = "int"

            inferred_params[clean_param] = ptype
            self._scope_variables[clean_param] = ptype
            self._declared_in_scope.add(clean_param)

        ret_type = self._resolve_type(node.return_type, default="int")

        defaults = getattr(node, "default_values", {}) or {}
        param_list = []
        for param in node.parameters:
            clean_param = self._sanitize_name(param)
            ptype = inferred_params[clean_param]
            if param in defaults:
                def_val = self.generate(defaults[param])
                param_list.append(f"{ptype} {clean_param} = {def_val}")
            else:
                param_list.append(f"{ptype} {clean_param}")

        params_str = ", ".join(param_list)

        func_name = self._sanitize_name(node.name)
        header = f"{self.get_indent()}{ret_type} {func_name}({params_str}) {{"

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
        """Generates a C++ struct/class definition."""
        class_name = self._sanitize_name(node.name)
        self._known_classes.add(class_name)
        extends_clause = f" : public {node.bases[0]}" if node.bases else ""
        header = f"{self.get_indent()}class {class_name}{extends_clause} {{\n{self.get_indent()}public:"

        self.indent()

        fields: Dict[str, str] = {}
        for stmt in node.body:
            if isinstance(stmt, IRFunction) and stmt.name == "__init__":
                for body_stmt in stmt.body:
                    if isinstance(body_stmt, IRAssignment) and body_stmt.target.startswith("self."):
                        attr_name = self._sanitize_name(body_stmt.target[5:])
                        val_type = self._infer_expression_type(body_stmt.value) or "int"
                        fields[attr_name] = val_type

        field_lines = [f"{self.get_indent()}{ftype} {fname};" for fname, ftype in fields.items()]

        member_lines: List[str] = []
        for stmt in node.body:
            if isinstance(stmt, IRFunction):
                if stmt.name == "__init__":
                    member_lines.append(self._generate_cpp_constructor(class_name, stmt))
                else:
                    member_lines.append(self._generate_cpp_instance_method(stmt))
            else:
                code = self.generate(stmt)
                if code:
                    member_lines.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")

        self.dedent()

        all_body = []
        if field_lines:
            all_body.extend(field_lines)
        if member_lines:
            all_body.extend(member_lines)

        body_str = "\n\n".join(all_body) if all_body else f"{self.get_indent()}    // Empty class"
        return f"{header}\n{body_str}\n{self.get_indent()}}};"

    def _generate_cpp_constructor(self, class_name: str, node: IRFunction) -> str:
        """Generates a C++ constructor from __init__."""
        prev_declared = set(self._declared_in_scope)
        prev_variables = dict(self._scope_variables)
        self._declared_in_scope.clear()
        self._scope_variables.clear()

        params = [p for p in node.parameters if p != "self"]
        param_types = getattr(node, "parameter_types", {}) or {}
        inferred_params = []
        for p in params:
            clean_p = self._sanitize_name(p)
            ptype = self._resolve_type(param_types.get(p), default="int")
            self._scope_variables[clean_p] = ptype
            self._declared_in_scope.add(clean_p)
            inferred_params.append(f"{ptype} {clean_p}")

        header = f"{self.get_indent()}{class_name}({', '.join(inferred_params)}) {{"
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

    def _generate_cpp_instance_method(self, node: IRFunction) -> str:
        """Generates a C++ member method."""
        prev_declared = set(self._declared_in_scope)
        prev_variables = dict(self._scope_variables)
        self._declared_in_scope.clear()
        self._scope_variables.clear()

        params = [p for p in node.parameters if p != "self"]
        param_types = getattr(node, "parameter_types", {}) or {}
        inferred_params = []
        for p in params:
            clean_p = self._sanitize_name(p)
            ptype = self._resolve_type(param_types.get(p), default="int")
            self._scope_variables[clean_p] = ptype
            self._declared_in_scope.add(clean_p)
            inferred_params.append(f"{ptype} {clean_p}")

        has_return_val = any(isinstance(s, IRReturn) and s.value is not None for s in node.body)
        ret_type = self._resolve_type(node.return_type, default="int" if has_return_val else "void")
        func_name = self._sanitize_name(node.name)

        header = f"{self.get_indent()}{ret_type} {func_name}({', '.join(inferred_params)}) {{"
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
        var_name = self._sanitize_name(node.name)
        if node.var_type:
            cpp_type = self._resolve_type(node.var_type)
            return f"{cpp_type} {var_name}"
        return var_name

    def generate_constant(self, node: IRConstant) -> str:
        """Generates a C++ literal constant."""
        if node.value is None:
            return "nullptr"
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, str):
            self._required_includes.add("#include <string>")
            escaped = (
                node.value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
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
        Infers local variable type on initial declaration and avoids duplicate type declarations.
        """
        if node.target.startswith("self."):
            attr = self._sanitize_name(node.target[5:])
            val_str = self.generate(node.value) if node.value else "0"
            return f"this->{attr} = {val_str};"

        if isinstance(node.value, IRListComprehension):
            comp = node.value
            self._required_includes.add("#include <vector>")
            elem_type = self._infer_expression_type(comp.element) or "int"
            target_name = self._sanitize_name(node.target)
            var_name_inner = self._sanitize_name(comp.variable)
            elt_code = self.generate(comp.element)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                loop = f"for (int {var_name_inner} = 0; {var_name_inner} < {limit}; ++{var_name_inner}) {{\n{self.get_indent()}    {cond_check}{target_name}.push_back({elt_code});\n{self.get_indent()}}}"
            else:
                iter_code = self.generate(comp.iterable)
                loop = f"for (const auto& {var_name_inner} : {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}.push_back({elt_code});\n{self.get_indent()}}}"

            decl = f"std::vector<{elem_type}> {target_name};\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        if isinstance(node.value, IRSetComprehension):
            comp = node.value
            self._required_includes.add("#include <set>")
            elem_type = self._infer_expression_type(comp.element) or "int"
            target_name = self._sanitize_name(node.target)
            var_name_inner = self._sanitize_name(comp.variable)
            elt_code = self.generate(comp.element)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                loop = f"for (int {var_name_inner} = 0; {var_name_inner} < {limit}; ++{var_name_inner}) {{\n{self.get_indent()}    {cond_check}{target_name}.insert({elt_code});\n{self.get_indent()}}}"
            else:
                iter_code = self.generate(comp.iterable)
                loop = f"for (const auto& {var_name_inner} : {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}.insert({elt_code});\n{self.get_indent()}}}"

            decl = f"std::set<{elem_type}> {target_name};\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        if isinstance(node.value, IRDictComprehension):
            comp = node.value
            self._required_includes.add("#include <map>")
            k_type = self._infer_expression_type(comp.key)
            if not k_type and isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                k_type = "int"
            k_type = k_type or "std::string"
            v_type = self._infer_expression_type(comp.value)
            if not v_type and isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                v_type = "int"
            v_type = v_type or "int"
            target_name = self._sanitize_name(node.target)
            k_code = self.generate(comp.key)
            v_code = self.generate(comp.value)
            cond_check = f"if ({self.generate(comp.condition)}) " if comp.condition else ""

            if isinstance(comp.iterable, IRFunctionCall) and comp.iterable.name == "range":
                limit = self.generate(comp.iterable.arguments[0])
                var_name_inner = self._sanitize_name(comp.variable.strip(" ()"))
                loop = f"for (int {var_name_inner} = 0; {var_name_inner} < {limit}; ++{var_name_inner}) {{\n{self.get_indent()}    {cond_check}{target_name}[{k_code}] = {v_code};\n{self.get_indent()}}}"
            elif "," in comp.variable:
                k_var, v_var = [self._sanitize_name(v.strip(" ()")) for v in comp.variable.split(",")]
                iter_code = self.generate(comp.iterable)
                if iter_code.endswith(".items()"):
                    iter_code = iter_code[:-8]
                loop = f"for (const auto& item_pair : {iter_code}) {{\n{self.get_indent()}    auto {k_var} = item_pair.first;\n{self.get_indent()}    auto {v_var} = item_pair.second;\n{self.get_indent()}    {cond_check}{target_name}[{k_code}] = {v_code};\n{self.get_indent()}}}"
            else:
                var_name_inner = self._sanitize_name(comp.variable.strip(" ()"))
                iter_code = self.generate(comp.iterable)
                loop = f"for (const auto& {var_name_inner} : {iter_code}) {{\n{self.get_indent()}    {cond_check}{target_name}[{k_code}] = {v_code};\n{self.get_indent()}}}"

            decl = f"std::map<{k_type}, {v_type}> {target_name};\n{self.get_indent()}{loop}"
            self._declared_in_scope.add(target_name)
            return decl

        var_name = self._sanitize_name(node.target)

        if node.value is None:
            if node.var_type:
                cpp_type = self._resolve_type(node.var_type)
                self._scope_variables[var_name] = cpp_type
                self._declared_in_scope.add(var_name)
                return f"{cpp_type} {var_name};"
            return f"int {var_name};"

        val_str = self.generate(node.value)

        if node.var_type:
            cpp_type = self._resolve_type(node.var_type)
            self._scope_variables[var_name] = cpp_type
            self._declared_in_scope.add(var_name)
            return f"{cpp_type} {var_name} = {val_str};"

        if var_name in self._declared_in_scope:
            return f"{var_name} = {val_str};"

        inferred_type = self._infer_expression_type(node.value)
        if inferred_type:
            self._scope_variables[var_name] = inferred_type
            self._declared_in_scope.add(var_name)
            return f"{inferred_type} {var_name} = {val_str};"

        self._scope_variables[var_name] = "auto"
        self._declared_in_scope.add(var_name)
        return f"auto {var_name} = {val_str};"

    def generate_tuple_assignment(self, node: IRTupleAssignment) -> str:
        """Generates multiple assignment / tuple unpacking in C++."""
        if isinstance(node.value, (IRTuple, IRList)):
            lines = []
            for target, val_node in zip(node.targets, node.value.elements):
                san_t = self._sanitize_name(target)
                lines.append(self.generate_assignment(IRAssignment(target=san_t, value=val_node)))
            return "\n".join(lines)
        else:
            self._required_includes.add("#include <tuple>")
            val_str = self.generate(node.value)
            lines = []
            for i, target in enumerate(node.targets):
                san_t = self._sanitize_name(target)
                if san_t not in self._declared_in_scope:
                    self._declared_in_scope.add(san_t)
                    lines.append(f"auto {san_t} = std::get<{i}>({val_str});")
                else:
                    lines.append(f"{san_t} = std::get<{i}>({val_str});")
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
        """Generates a C++ for loop (handles range(), enumerate(), zip(), range-based for, pair unpacking, and loop else)."""
        indent_str = self.get_indent()
        break_flag = "_completed" if node.else_body else None

        if "," in node.variable and isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "enumerate":
            targets = [self._sanitize_name(x.strip(" ()")) for x in node.variable.split(",")]
            idx_var, val_var = targets[0], targets[1]
            coll_str = self.generate(node.iterable.arguments[0])
            loop_header = f"for (int {idx_var} = 0; {idx_var} < static_cast<int>({coll_str}.size()); ++{idx_var})"
            self.indent()
            body_lines = [f"auto {val_var} = {coll_str}[{idx_var}];"]
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
            self._required_includes.add("#include <algorithm>")
            loop_header = f"for (int {idx_var} = 0; {idx_var} < static_cast<int>(std::min({xs_str}.size(), {ys_str}.size())); ++{idx_var})"
            self.indent()
            body_lines = [
                f"auto {var_a} = {xs_str}[{idx_var}];",
                f"auto {var_b} = {ys_str}[{idx_var}];",
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
                iter_str = iter_str[:-8]
            loop_header = f"for (const auto& item_pair : {iter_str})"
            self.indent()
            body_lines = [
                f"auto {k_var} = item_pair.first;",
                f"auto {v_var} = item_pair.second;",
            ]
            self._declared_in_scope.add(k_var)
            self._declared_in_scope.add(v_var)
            for s in node.body:
                code = self._render_statement_with_flag(s, break_flag) if break_flag else self.generate(s)
                if code:
                    body_lines.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
            body_str = "\n".join(body_lines)
            self.dedent()
            loop_code = f"{indent_str}{loop_header} {{\n{body_str}\n{indent_str}}}"

        elif isinstance(node.iterable, IRFunctionCall) and node.iterable.name == "range":
            var_name = self._sanitize_name(node.variable)
            args = node.iterable.arguments
            if len(args) == 1:
                start_val = "0"
                stop_val = self.generate(args[0])
                loop_header = f"for (int {var_name} = {start_val}; {var_name} < {stop_val}; ++{var_name})"
            elif len(args) == 2:
                start_val = self.generate(args[0])
                stop_val = self.generate(args[1])
                loop_header = f"for (int {var_name} = {start_val}; {var_name} < {stop_val}; ++{var_name})"
            elif len(args) >= 3:
                start_val = self.generate(args[0])
                stop_val = self.generate(args[1])
                step_val = self.generate(args[2])
                if step_val.strip().startswith("-"):
                    loop_header = f"for (int {var_name} = {start_val}; {var_name} > {stop_val}; {var_name} += {step_val})"
                else:
                    loop_header = f"for (int {var_name} = {start_val}; {var_name} < {stop_val}; {var_name} += {step_val})"
            else:
                start_val = "0"
                stop_val = "0"
                loop_header = f"for (int {var_name} = {start_val}; {var_name} < {stop_val}; ++{var_name})"
            self._scope_variables[var_name] = "int"
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
            loop_header = f"for (const auto& {var_name} : {iter_str})"
            self._scope_variables[var_name] = "auto"
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
            return f"{indent_str}bool _completed = true;\n{loop_code}\n{indent_str}if (_completed) {{\n{else_str}\n{indent_str}}}"

        return loop_code

    def generate_while(self, node: IRWhile) -> str:
        """Generates a C++ while loop (including while/else lowering)."""
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
            return f"{indent_str}bool _completed = true;\n{loop_code}\n{indent_str}if (_completed) {{\n{else_str}\n{indent_str}}}"

        return loop_code

    def generate_break(self, node: IRBreak) -> str:
        """Generates a C++ break statement."""
        return "break;"

    def generate_continue(self, node: IRContinue) -> str:
        """Generates a C++ continue statement."""
        return "continue;"

    def generate_assert(self, node: IRAssert) -> str:
        """Generates a C++ assertion statement."""
        self._required_includes.add("#include <stdexcept>")
        indent_str = self.get_indent()
        cond_str = self.generate(node.condition)
        if node.message:
            msg_str = self.generate(node.message)
            return f"{indent_str}if (!({cond_str})) throw std::runtime_error({msg_str});"
        return f"{indent_str}if (!({cond_str})) throw std::runtime_error(\"Assertion failed\");"

    def generate_yield(self, node: IRYield) -> str:
        """Generates code for a yield statement/expression in C++."""
        val_str = self.generate(node.value) if node.value else ""
        return f"/* yield */ {val_str};"

    def generate_generator_expression(self, node: IRGeneratorExpression) -> str:
        """Generates C++ vector collection via lambda from generator expression."""
        self._required_includes.add("#include <vector>")
        var_name = self._sanitize_name(node.variable.strip(" ()"))
        elt_str = self.generate(node.element)
        iter_str = self.generate(node.iterable)
        if node.condition:
            cond_str = self.generate(node.condition)
            return f"([&]{{ auto _res = std::vector<decltype({elt_str})>{{}}; for (const auto& {var_name} : {iter_str}) if ({cond_str}) _res.push_back({elt_str}); return _res; }}())"
        return f"([&]{{ auto _res = std::vector<decltype({elt_str})>{{}}; for (const auto& {var_name} : {iter_str}) _res.push_back({elt_str}); return _res; }}())"

    def generate_starred(self, node: IRStarred) -> str:
        """Generates code for a starred argument (*args or **kwargs)."""
        return self.generate(node.value)

    def generate_isinstance(self, node: IRIsInstance) -> str:
        """Generates a C++ type check expression."""
        return "true"

    def generate_try(self, node: IRTry) -> str:
        """Generates a C++ try-catch block (including multiple handlers and try/else)."""
        indent_str = self.get_indent()
        out = []

        if node.else_body:
            out.append(f"{indent_str}bool _try_ok = true;")

        out.append(f"{indent_str}try {{")
        self.indent()
        for s in node.body:
            code = self.generate(s)
            if code:
                out.append(code if code.startswith(" ") else f"{self.get_indent()}{code}")
        self.dedent()
        out.append(f"{indent_str}}}")

        self._required_includes.add("#include <exception>")
        self._required_includes.add("#include <stdexcept>")

        exc_map = {
            "ValueError": "const std::invalid_argument&",
            "TypeError": "const std::runtime_error&",
            "IndexError": "const std::out_of_range&",
            "KeyError": "const std::out_of_range&",
            "Exception": "const std::exception&",
            "BaseException": "const std::exception&",
        }

        for i, h in enumerate(node.handlers):
            exc_type = exc_map.get(h.exception_type, "const std::exception&") if h.exception_type else "const std::exception&"
            alias = self._sanitize_name(h.alias) if h.alias else ("e" if len(node.handlers) == 1 else f"e_{i}")
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

        if node.finally_body:
            for s in node.finally_body:
                code = self.generate(s)
                if code:
                    out.append(code if code.startswith(" ") else f"{indent_str}{code}")

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
        """Generates a C++ throw statement."""
        self._required_includes.add("#include <stdexcept>")
        if node.exception:
            exc_code = self.generate(node.exception)
            return f"throw std::runtime_error({exc_code});"
        return "throw;"

    def generate_binary_operation(self, node: IRBinaryOperation) -> str:
        """Generates a binary operation with mapped C++ operators (including 'is', 'is not', 'in' / 'not in')."""
        if node.operator == "is":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in ("nullptr", "None", "NULL") or (isinstance(node.right, IRConstant) and node.right.value is None):
                return f"({left_str} == nullptr)"
            if left_str in ("nullptr", "None", "NULL") or (isinstance(node.left, IRConstant) and node.left.value is None):
                return f"({right_str} == nullptr)"
            return f"({left_str} == {right_str})"

        if node.operator == "is not":
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in ("nullptr", "None", "NULL") or (isinstance(node.right, IRConstant) and node.right.value is None):
                return f"({left_str} != nullptr)"
            if left_str in ("nullptr", "None", "NULL") or (isinstance(node.left, IRConstant) and node.left.value is None):
                return f"({right_str} != nullptr)"
            return f"({left_str} != {right_str})"

        if node.operator == "in":
            self._required_includes.add("#include <algorithm>")
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in self._scope_variables and (self._scope_variables[right_str].startswith("std::map") or self._scope_variables[right_str].startswith("std::set")):
                return f"({right_str}.find({left_str}) != {right_str}.end())"
            if right_str in self._scope_variables and self._scope_variables[right_str] == "std::string":
                return f"({right_str}.find({left_str}) != std::string::npos)"
            return f"(std::find({right_str}.begin(), {right_str}.end(), {left_str}) != {right_str}.end())"

        if node.operator == "not in":
            self._required_includes.add("#include <algorithm>")
            left_str = self.generate(node.left)
            right_str = self.generate(node.right)
            if right_str in self._scope_variables and (self._scope_variables[right_str].startswith("std::map") or self._scope_variables[right_str].startswith("std::set")):
                return f"({right_str}.find({left_str}) == {right_str}.end())"
            if right_str in self._scope_variables and self._scope_variables[right_str] == "std::string":
                return f"({right_str}.find({left_str}) == std::string::npos)"
            return f"(std::find({right_str}.begin(), {right_str}.end(), {left_str}) == {right_str}.end())"

        left_str = self.generate(node.left)
        op_str = CPP_OPERATOR_MAP.get(node.operator, node.operator)
        right_str = self.generate(node.right)
        return f"{left_str} {op_str} {right_str}"

    def generate_chained_comparison(self, node: IRChainedComparison) -> str:
        """Generates a chained comparison expression (e.g. 1 < x < 10 -> (1 < x) && (x < 10))."""
        comparisons = []
        for i in range(len(node.operators)):
            left = self.generate(node.operands[i])
            op = CPP_OPERATOR_MAP.get(node.operators[i], node.operators[i])
            right = self.generate(node.operands[i + 1])
            comparisons.append(f"({left} {op} {right})")
        return " && ".join(comparisons)

    def generate_lambda(self, node: IRLambda) -> str:
        """Generates a C++ lambda expression."""
        params_str = ", ".join([f"auto {self._sanitize_name(p)}" for p in node.parameters])
        body_str = self.generate(node.body)
        return f"[&]({params_str}) {{ return {body_str}; }}"

    def generate_unary_operation(self, node: IRUnaryOperation) -> str:
        """Generates a unary operation (e.g. !flag, -x)."""
        op_str = CPP_OPERATOR_MAP.get(node.operator, node.operator)
        operand_str = self.generate(node.operand)
        return f"{op_str}{operand_str}"

    def generate_function_call(self, node: IRFunctionCall) -> str:
        """
        Generates a function call.
        Maps Python built-ins, reduction operations, and standard library functions to C++ standard library.
        """
        if node.name == "sum" and len(node.arguments) == 1 and isinstance(node.arguments[0], IRGeneratorExpression):
            gen = node.arguments[0]
            var = self._sanitize_name(gen.variable.strip(" ()"))
            elt = self.generate(gen.element)
            iter_c = self.generate(gen.iterable)
            cond_c = f"if ({self.generate(gen.condition)}) " if gen.condition else ""
            return f"([&]{{ auto _sum = 0; for (const auto& {var} : {iter_c}) {cond_c}_sum += {elt}; return _sum; }}())"

        if node.name == "any" and len(node.arguments) == 1 and isinstance(node.arguments[0], IRGeneratorExpression):
            gen = node.arguments[0]
            var = self._sanitize_name(gen.variable.strip(" ()"))
            elt = self.generate(gen.element)
            iter_c = self.generate(gen.iterable)
            return f"([&]{{ for (const auto& {var} : {iter_c}) if ({elt}) return true; return false; }}())"

        if node.name == "all" and len(node.arguments) == 1 and isinstance(node.arguments[0], IRGeneratorExpression):
            gen = node.arguments[0]
            var = self._sanitize_name(gen.variable.strip(" ()"))
            elt = self.generate(gen.element)
            iter_c = self.generate(gen.iterable)
            return f"([&]{{ for (const auto& {var} : {iter_c}) if (!({elt})) return false; return true; }}())"

        args_list = [self.generate(arg) for arg in node.arguments]
        if node.keywords:
            args_list.extend([self.generate(v) for v in node.keywords.values()])
        args_str = ", ".join(args_list)

        if node.name == "print":
            self._required_includes.add("#include <iostream>")
            if not node.arguments:
                return "std::cout << std::endl"
            args_stream = " << ".join(args_list)
            return f"std::cout << {args_stream} << std::endl"

        if node.name == "len" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"{arg_str}.size()"

        if node.name == "abs" and len(node.arguments) == 1:
            self._required_includes.add("#include <cmath>")
            arg_str = self.generate(node.arguments[0])
            return f"std::abs({arg_str})"

        if node.name == "map" and len(node.arguments) == 2:
            fn_str = self.generate(node.arguments[0])
            iter_str = self.generate(node.arguments[1])
            return f"([&]{{ auto _res = {iter_str}; for (auto& _x : _res) _x = {fn_str}(_x); return _res; }}())"

        if node.name == "filter" and len(node.arguments) == 2:
            self._required_includes.add("#include <algorithm>")
            fn_str = self.generate(node.arguments[0])
            iter_str = self.generate(node.arguments[1])
            return f"([&]{{ auto _res = {iter_str}; _res.erase(std::remove_if(_res.begin(), _res.end(), [&](const auto& _x){{ return !{fn_str}(_x); }}), _res.end()); return _res; }}())"

        math_resolved = ModuleMappingRegistry.resolve_math_call("cpp", node.name, args_str)
        if math_resolved:
            code, inc = math_resolved
            if inc:
                self._required_includes.add(inc)
            return code

        builtin_resolved = ModuleMappingRegistry.resolve_builtin_call("cpp", node.name, args_list)
        if builtin_resolved:
            code, inc = builtin_resolved
            if inc:
                self._required_includes.add(inc)
            return code

        if node.name == "sorted" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            self._required_includes.add("#include <algorithm>")
            self._required_includes.add("#include <vector>")
            return f"([&]{{ auto _s = {arg_str}; std::sort(_s.begin(), _s.end()); return _s; }}())"

        if node.name == "reversed" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            self._required_includes.add("#include <algorithm>")
            self._required_includes.add("#include <vector>")
            return f"([&]{{ auto _r = {arg_str}; std::reverse(_r.begin(), _r.end()); return _r; }}())"

        if node.name == "min" and len(node.arguments) >= 2:
            self._required_includes.add("#include <algorithm>")
            if len(node.arguments) == 2:
                arg1 = self.generate(node.arguments[0])
                arg2 = self.generate(node.arguments[1])
                return f"std::min({arg1}, {arg2})"
            else:
                args = ", ".join([self.generate(arg) for arg in node.arguments])
                return f"std::min({{{args}}})"

        if node.name == "max" and len(node.arguments) >= 2:
            self._required_includes.add("#include <algorithm>")
            if len(node.arguments) == 2:
                arg1 = self.generate(node.arguments[0])
                arg2 = self.generate(node.arguments[1])
                return f"std::max({arg1}, {arg2})"
            else:
                args = ", ".join([self.generate(arg) for arg in node.arguments])
                return f"std::max({{{args}}})"

        if node.name == "str" and len(node.arguments) == 1:
            self._required_includes.add("#include <string>")
            arg_str = self.generate(node.arguments[0])
            return f"std::to_string({arg_str})"

        if node.name == "int" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"static_cast<int>({arg_str})"

        if node.name == "float" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"static_cast<double>({arg_str})"

        if node.name == "bool" and len(node.arguments) == 1:
            arg_str = self.generate(node.arguments[0])
            return f"static_cast<bool>({arg_str})"

        if "." in node.name:
            obj_name, method_name = node.name.rsplit(".", 1)
            if obj_name == "self":
                obj_name = "this"
            else:
                obj_name = self._sanitize_name(obj_name)

            if method_name == "append" and len(node.arguments) == 1:
                return f"{obj_name}.push_back({self.generate(node.arguments[0])})"
            elif method_name == "add" and len(node.arguments) == 1:
                if self._scope_variables.get(obj_name, "").startswith("std::set") or obj_name.startswith("set") or obj_name == "s":
                    return f"{obj_name}.insert({self.generate(node.arguments[0])})"
                return f"{obj_name}.add({self.generate(node.arguments[0])})"
            elif method_name == "pop" and not node.arguments:
                return f"{obj_name}.pop_back()"
            elif method_name == "remove" and len(node.arguments) == 1:
                return f"{obj_name}.erase({self.generate(node.arguments[0])})"
            elif method_name == "discard" and len(node.arguments) == 1:
                return f"{obj_name}.erase({self.generate(node.arguments[0])})"
            elif method_name == "extend" and len(node.arguments) == 1:
                arg_str = self.generate(node.arguments[0])
                return f"{obj_name}.insert({obj_name}.end(), {arg_str}.begin(), {arg_str}.end())"
            elif method_name == "insert" and len(node.arguments) == 2:
                idx = self.generate(node.arguments[0])
                el = self.generate(node.arguments[1])
                return f"{obj_name}.insert({obj_name}.begin() + ({idx}), {el})"
            elif method_name == "index" and len(node.arguments) == 1:
                self._required_includes.add("#include <algorithm>")
                el = self.generate(node.arguments[0])
                return f"static_cast<int>(std::distance({obj_name}.begin(), std::find({obj_name}.begin(), {obj_name}.end(), {el})))"
            elif method_name == "reverse" and not node.arguments:
                self._required_includes.add("#include <algorithm>")
                return f"std::reverse({obj_name}.begin(), {obj_name}.end())"
            elif method_name == "sort" and not node.arguments:
                self._required_includes.add("#include <algorithm>")
                return f"std::sort({obj_name}.begin(), {obj_name}.end())"
            elif method_name == "count" and len(node.arguments) == 1:
                self._required_includes.add("#include <algorithm>")
                el = self.generate(node.arguments[0])
                return f"static_cast<int>(std::count({obj_name}.begin(), {obj_name}.end(), {el}))"

            elif method_name in ("upper", "lower", "strip") and not node.arguments:
                return f"{obj_name}"
            elif method_name == "startswith" and len(node.arguments) == 1:
                prefix = self.generate(node.arguments[0])
                return f"({obj_name}.rfind({prefix}, 0) == 0)"
            elif method_name == "endswith" and len(node.arguments) == 1:
                suffix = self.generate(node.arguments[0])
                return f"({obj_name}.length() >= {suffix}.length() && {obj_name}.compare({obj_name}.length() - {suffix}.length(), {suffix}.length(), {suffix}) == 0)"
            elif method_name == "find" and len(node.arguments) == 1:
                sub = self.generate(node.arguments[0])
                return f"static_cast<int>({obj_name}.find({sub}))"

            elif method_name == "get":
                k = self.generate(node.arguments[0])
                d = self.generate(node.arguments[1]) if len(node.arguments) == 2 else "0"
                return f"({obj_name}.count({k}) ? {obj_name}[{k}] : {d})"
            elif method_name == "setdefault" and len(node.arguments) >= 2:
                k = self.generate(node.arguments[0])
                v = self.generate(node.arguments[1])
                return f"([&]{{ if ({obj_name}.find({k}) == {obj_name}.end()) {obj_name}[{k}] = {v}; return {obj_name}[{k}]; }}())"
            elif method_name == "keys" and not node.arguments:
                self._required_includes.add("#include <vector>")
                return f"([&]{{ auto _k = std::vector<decltype({obj_name}.begin()->first)>{{}}; for (const auto& _p : {obj_name}) _k.push_back(_p.first); return _k; }}())"
            elif method_name == "values" and not node.arguments:
                self._required_includes.add("#include <vector>")
                return f"([&]{{ auto _v = std::vector<decltype({obj_name}.begin()->second)>{{}}; for (const auto& _p : {obj_name}) _v.push_back(_p.second); return _v; }}())"
            elif method_name == "items" and not node.arguments:
                return f"{obj_name}"

        func_name = self._sanitize_name(node.name)
        return f"{func_name}({args_str})"

    def generate_subscript(self, node: IRSubscript) -> str:
        """Generates C++ array/vector/map indexing or string slicing."""
        val_str = self.generate(node.value)
        if isinstance(node.slice, IRSlice):
            lower = self.generate(node.slice.lower) if node.slice.lower else "0"
            if node.slice.upper:
                upper = self.generate(node.slice.upper)
                return f"{val_str}.substr({lower}, {upper} - ({lower}))"
            else:
                return f"{val_str}.substr({lower})"

        idx_str = self.generate(node.slice)
        return f"{val_str}[{idx_str}]"

    def generate_slice(self, node: IRSlice) -> str:
        """Generates a slice string representation."""
        lower = self.generate(node.lower) if node.lower else "0"
        upper = self.generate(node.upper) if node.upper else ""
        return f"{lower}:{upper}"

    def generate_attribute(self, node: IRAttribute) -> str:
        """Generates C++ member/field access or math constants."""
        if isinstance(node.value, IRName) and node.value.name == "self":
            return f"this->{self._sanitize_name(node.attribute)}"
        val_str = self.generate(node.value)
        attr = self._sanitize_name(node.attribute)
        const_resolved = ModuleMappingRegistry.resolve_math_constant("cpp", f"{val_str}.{node.attribute}")
        if const_resolved:
            code, inc = const_resolved
            if inc:
                self._required_includes.add(inc)
            return code
        return f"{val_str}.{attr}"

    def generate_list_comprehension(self, node: IRListComprehension) -> str:
        """Generates code for list comprehension."""
        return "std::vector<int>{}"

    def generate_set_comprehension(self, node: IRSetComprehension) -> str:
        """Generates code for set comprehension."""
        return "std::set<int>{}"

    def generate_dict_comprehension(self, node: IRDictComprehension) -> str:
        """Generates code for dict comprehension."""
        return "std::map<std::string, int>{}"

    def generate_list(self, node: IRList) -> str:
        """Generates C++ std::vector initialization."""
        self._required_includes.add("#include <vector>")
        if not node.elements:
            return "std::vector<int>{}"

        elem_type = self._infer_expression_type(node.elements[0]) or "int"
        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"std::vector<{elem_type}>{{{elements_str}}}"

    def generate_tuple(self, node: IRTuple) -> str:
        """Generates C++ std::make_tuple."""
        self._required_includes.add("#include <tuple>")
        if not node.elements:
            return "std::make_tuple()"
        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"std::make_tuple({elements_str})"

    def generate_set(self, node: IRSet) -> str:
        """Generates C++ std::set initialization."""
        self._required_includes.add("#include <set>")
        if not node.elements:
            return "std::set<int>{}"

        elem_type = self._infer_expression_type(node.elements[0]) or "int"
        elements_str = ", ".join([self.generate(el) for el in node.elements])
        return f"std::set<{elem_type}>{{{elements_str}}}"

    def generate_dict(self, node: IRDict) -> str:
        """Generates C++ std::map initialization."""
        self._required_includes.add("#include <map>")
        if not node.keys:
            return "std::map<std::string, int>{}"

        k_type = self._infer_expression_type(node.keys[0]) or "std::string"
        v_type = self._infer_expression_type(node.values[0]) or "int"

        pairs = [
            f"{{{self.generate(k)}, {self.generate(v)}}}"
            for k, v in zip(node.keys, node.values)
        ]
        return f"std::map<{k_type}, {v_type}>{{{', '.join(pairs)}}}"
