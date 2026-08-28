from typing import Dict, Optional, Tuple


class ModuleMappingRegistry:

    MATH_FUNCTIONS: Dict[str, Tuple[str, str, str, str]] = {
        "sqrt": ("Math.sqrt", "std::sqrt", "Math.sqrt", "#include <cmath>"),
        "pow": ("Math.pow", "std::pow", "Math.pow", "#include <cmath>"),
        "ceil": ("Math.ceil", "std::ceil", "Math.ceil", "#include <cmath>"),
        "floor": ("Math.floor", "std::floor", "Math.floor", "#include <cmath>"),
        "abs": ("Math.abs", "std::abs", "Math.abs", "#include <cmath>"),
        "fabs": ("Math.abs", "std::abs", "Math.abs", "#include <cmath>"),
        "sin": ("Math.sin", "std::sin", "Math.sin", "#include <cmath>"),
        "cos": ("Math.cos", "std::cos", "Math.cos", "#include <cmath>"),
        "tan": ("Math.tan", "std::tan", "Math.tan", "#include <cmath>"),
        "log": ("Math.log", "std::log", "Math.log", "#include <cmath>"),
        "exp": ("Math.exp", "std::exp", "Math.exp", "#include <cmath>"),
    }

    MATH_CONSTANTS: Dict[str, Tuple[str, str, str]] = {
        "pi": ("Math.PI", "M_PI", "Math.PI"),
        "e": ("Math.E", "M_E", "Math.E"),
    }

    @classmethod
    def resolve_math_call(cls, target_lang: str, func_name: str, args_str: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Resolves a math function call (e.g. math.sqrt or bare sqrt if imported).
        Returns (code_snippet, required_cpp_include) or None.
        """
        clean_func = func_name.replace("math.", "")
        if clean_func in cls.MATH_FUNCTIONS:
            java_map, cpp_map, js_map, cpp_inc = cls.MATH_FUNCTIONS[clean_func]
            if target_lang == "java":
                return f"{java_map}({args_str})", None
            elif target_lang == "cpp":
                return f"{cpp_map}({args_str})", cpp_inc
            elif target_lang == "javascript":
                return f"{js_map}({args_str})", None
        return None

    @classmethod
    def resolve_math_constant(cls, target_lang: str, attr_name: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Resolves math constants (e.g. math.pi, math.e).
        Returns (code_snippet, required_cpp_include) or None.
        """
        clean_attr = attr_name.replace("math.", "").lower()
        if clean_attr in cls.MATH_CONSTANTS:
            java_map, cpp_map, js_map = cls.MATH_CONSTANTS[clean_attr]
            if target_lang == "java":
                return java_map, None
            elif target_lang == "cpp":
                return cpp_map, "#include <cmath>"
            elif target_lang == "javascript":
                return js_map, None
        return None

    @classmethod
    def resolve_builtin_call(cls, target_lang: str, func_name: str, args_list: list) -> Optional[Tuple[str, Optional[str]]]:
        """
        Resolves built-in aggregation/iterator functions (any, all, sum, etc.).
        Returns (code_snippet, required_cpp_include) or None.
        """
        if not args_list:
            return None

        arg0 = args_list[0]
        if func_name == "sum" and len(args_list) == 1:
            if target_lang == "java":
                return f"{arg0}.stream().mapToInt(Integer::intValue).sum()", None
            elif target_lang == "cpp":
                return f"std::accumulate({arg0}.begin(), {arg0}.end(), 0)", "#include <numeric>"
            elif target_lang == "javascript":
                return f"{arg0}.reduce((a, b) => a + b, 0)", None

        elif func_name == "any" and len(args_list) == 1:
            if target_lang == "java":
                return f"{arg0}.stream().anyMatch(Boolean::booleanValue)", None
            elif target_lang == "cpp":
                return f"std::any_of({arg0}.begin(), {arg0}.end(), [](bool v){{ return v; }})", "#include <algorithm>"
            elif target_lang == "javascript":
                return f"{arg0}.some(Boolean)", None

        elif func_name == "all" and len(args_list) == 1:
            if target_lang == "java":
                return f"{arg0}.stream().allMatch(Boolean::booleanValue)", None
            elif target_lang == "cpp":
                return f"std::all_of({arg0}.begin(), {arg0}.end(), [](bool v){{ return v; }})", "#include <algorithm>"
            elif target_lang == "javascript":
                return f"{arg0}.every(Boolean)", None

        elif func_name == "callable" and len(args_list) == 1:
            if target_lang == "java":
                return f"({arg0} != null)", None
            elif target_lang == "cpp":
                return "true", None
            elif target_lang == "javascript":
                return f"(typeof {arg0} === 'function')", None

        elif func_name == "type" and len(args_list) == 1:
            if target_lang == "java":
                return f"{arg0}.getClass().getSimpleName()", None
            elif target_lang == "cpp":
                return f"typeid({arg0}).name()", "#include <typeinfo>"
            elif target_lang == "javascript":
                return f"typeof {arg0}", None

        elif func_name == "hasattr" and len(args_list) == 2:
            obj, prop = args_list[0], args_list[1]
            if target_lang == "java":
                return f"({obj} != null)", None
            elif target_lang == "cpp":
                return "true", None
            elif target_lang == "javascript":
                return f"({obj} != null && ({prop} in {obj} || {obj}.hasOwnProperty({prop})))", None

        elif func_name == "getattr" and len(args_list) >= 2:
            obj, prop = args_list[0], args_list[1]
            default_val = args_list[2] if len(args_list) >= 3 else "null"
            if target_lang == "java":
                clean_prop = prop.strip("\"'")
                return f"{obj}.{clean_prop}", None
            elif target_lang == "cpp":
                clean_prop = prop.strip("\"'")
                return f"{obj}.{clean_prop}", None
            elif target_lang == "javascript":
                return f"({obj}[{prop}] !== undefined ? {obj}[{prop}] : {default_val})", None

        return None
