import ast
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple


class ComplexityRank(IntEnum):
    CONSTANT = 0
    LOGARITHMIC = 1
    LINEAR = 2
    LINEARITHMIC = 3
    QUADRATIC = 4
    CUBIC = 5
    EXPONENTIAL = 6
    FACTORIAL = 7
    UNKNOWN = 99


COMPLEXITY_NOTATIONS: Dict[ComplexityRank, str] = {
    ComplexityRank.CONSTANT: "O(1)",
    ComplexityRank.LOGARITHMIC: "O(log n)",
    ComplexityRank.LINEAR: "O(n)",
    ComplexityRank.LINEARITHMIC: "O(n log n)",
    ComplexityRank.QUADRATIC: "O(n^2)",
    ComplexityRank.CUBIC: "O(n^3)",
    ComplexityRank.EXPONENTIAL: "O(2^n)",
    ComplexityRank.FACTORIAL: "O(n!)",
    ComplexityRank.UNKNOWN: "Unknown / requires deeper analysis",
}


@dataclass
class ComplexityResult:
    time_complexity: str
    time_explanation: str
    space_complexity: str
    space_explanation: str
    time_rank: ComplexityRank = ComplexityRank.CONSTANT
    space_rank: ComplexityRank = ComplexityRank.CONSTANT


class ComplexityAnalyzer:
    def analyze(self, source_code: str) -> ComplexityResult:
        if not source_code or not source_code.strip():
            return ComplexityResult(
                time_complexity="O(1)",
                time_explanation="Empty source code performs no operations.",
                space_complexity="O(1)",
                space_explanation="Empty source code uses no auxiliary memory.",
                time_rank=ComplexityRank.CONSTANT,
                space_rank=ComplexityRank.CONSTANT,
            )

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            line_info = f" on line {e.lineno}" if e.lineno else ""
            raise ValueError(f"Syntax error{line_info}: {e.msg or str(e)}")

        return self.analyze_ast(tree)

    def analyze_ast(self, tree: ast.AST) -> ComplexityResult:
        functions = [n for n in getattr(tree, "body", []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]

        func_names = {f.name for f in functions}
        for cls in classes:
            for n in cls.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_names.add(n.name)

        time_ranks: List[Tuple[ComplexityRank, str]] = []
        space_ranks: List[Tuple[ComplexityRank, str]] = []

        top_stmts = [n for n in getattr(tree, "body", []) if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        if top_stmts:
            t_rank, t_reason, s_rank, s_reason = self._analyze_block(top_stmts, current_func=None, all_funcs=func_names)
            time_ranks.append((t_rank, t_reason))
            space_ranks.append((s_rank, s_reason))

        for func in functions:
            t_rank, t_reason, s_rank, s_reason = self._analyze_function(func, all_funcs=func_names)
            time_ranks.append((t_rank, f"In function '{func.name}': {t_reason}"))
            space_ranks.append((s_rank, f"In function '{func.name}': {s_reason}"))

        for cls in classes:
            for n in cls.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    t_rank, t_reason, s_rank, s_reason = self._analyze_function(n, all_funcs=func_names)
                    time_ranks.append((t_rank, f"In method '{cls.name}.{n.name}': {t_reason}"))
                    space_ranks.append((s_rank, f"In method '{cls.name}.{n.name}': {s_reason}"))

        if not time_ranks:
            return ComplexityResult(
                time_complexity="O(1)",
                time_explanation="The program executes constant time O(1) declarations.",
                space_complexity="O(1)",
                space_explanation="Only constant O(1) memory is allocated.",
                time_rank=ComplexityRank.CONSTANT,
                space_rank=ComplexityRank.CONSTANT,
            )

        unknown_times = [r for r in time_ranks if r[0] == ComplexityRank.UNKNOWN]
        known_times = [r for r in time_ranks if r[0] != ComplexityRank.UNKNOWN]

        if unknown_times and not known_times:
            final_time_rank = ComplexityRank.UNKNOWN
            final_time_exp = unknown_times[0][1]
        elif known_times:
            max_time = max(known_times, key=lambda x: x[0])
            final_time_rank = max_time[0]
            final_time_exp = max_time[1]
        else:
            final_time_rank = ComplexityRank.CONSTANT
            final_time_exp = "Only constant-time statements were detected."

        unknown_spaces = [r for r in space_ranks if r[0] == ComplexityRank.UNKNOWN]
        known_spaces = [r for r in space_ranks if r[0] != ComplexityRank.UNKNOWN]

        if unknown_spaces and not known_spaces:
            final_space_rank = ComplexityRank.UNKNOWN
            final_space_exp = unknown_spaces[0][1]
        elif known_spaces:
            max_space = max(known_spaces, key=lambda x: x[0])
            final_space_rank = max_space[0]
            final_space_exp = max_space[1]
        else:
            final_space_rank = ComplexityRank.CONSTANT
            final_space_exp = "Only constant-size scalar variables are allocated."

        return ComplexityResult(
            time_complexity=COMPLEXITY_NOTATIONS.get(final_time_rank, "Unknown / requires deeper analysis"),
            time_explanation=final_time_exp,
            space_complexity=COMPLEXITY_NOTATIONS.get(final_space_rank, "Unknown / requires deeper analysis"),
            space_explanation=final_space_exp,
            time_rank=final_time_rank,
            space_rank=final_space_rank,
        )


    def _analyze_function(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        all_funcs: Set[str],
    ) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        rec_info = self._detect_recursion(func_node)
        if rec_info["is_recursive"]:
            return (
                rec_info["time_rank"],
                rec_info["time_explanation"],
                rec_info["space_rank"],
                rec_info["space_explanation"],
            )

        return self._analyze_block(func_node.body, current_func=func_node.name, all_funcs=all_funcs)

    def _analyze_block(
        self,
        statements: List[ast.stmt],
        current_func: Optional[str],
        all_funcs: Set[str],
    ) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        max_time_rank = ComplexityRank.CONSTANT
        time_reasons: List[str] = []

        max_space_rank = ComplexityRank.CONSTANT
        space_reasons: List[str] = []

        sequential_loop_count = 0

        for stmt in statements:
            t_rank, t_reason, s_rank, s_reason = self._analyze_statement(stmt, current_func, all_funcs)

            if t_rank == ComplexityRank.UNKNOWN:
                return ComplexityRank.UNKNOWN, t_reason, ComplexityRank.UNKNOWN, s_reason

            if t_rank == ComplexityRank.LINEAR:
                sequential_loop_count += 1

            if t_rank > max_time_rank:
                max_time_rank = t_rank
                time_reasons = [t_reason]
            elif t_rank == max_time_rank and t_rank > ComplexityRank.CONSTANT:
                time_reasons.append(t_reason)

            if s_rank > max_space_rank:
                max_space_rank = s_rank
                space_reasons = [s_reason]
            elif s_rank == max_space_rank and s_rank > ComplexityRank.CONSTANT:
                space_reasons.append(s_reason)

        if max_time_rank == ComplexityRank.CONSTANT:
            t_explanation = "The code consists of sequential basic operations without variable loops or recursion."
        elif max_time_rank == ComplexityRank.LINEAR and sequential_loop_count > 1:
            t_explanation = f"The code contains {sequential_loop_count} sequential loops, resulting in O(n) dominant time complexity."
        else:
            t_explanation = time_reasons[0] if time_reasons else "Iterative linear operations executed."

        if max_space_rank == ComplexityRank.CONSTANT:
            s_explanation = "Only constant-size variables are used and no additional data structure grows with input size."
        else:
            s_explanation = space_reasons[0] if space_reasons else "Dynamic memory structures scale with input size."

        return max_time_rank, t_explanation, max_space_rank, s_explanation

    def _analyze_statement(
        self,
        stmt: ast.stmt,
        current_func: Optional[str],
        all_funcs: Set[str],
    ) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        if isinstance(stmt, (ast.For, ast.AsyncFor)):
            return self._analyze_for_loop(stmt, current_func, all_funcs)
        elif isinstance(stmt, ast.While):
            return self._analyze_while_loop(stmt, current_func, all_funcs)
        elif isinstance(stmt, ast.If):
            return self._analyze_if(stmt, current_func, all_funcs)
        elif isinstance(stmt, ast.Try):
            return self._analyze_try(stmt, current_func, all_funcs)
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            return self._analyze_assignment(stmt)
        elif isinstance(stmt, ast.Expr):
            return self._analyze_expr_stmt(stmt)
        elif isinstance(stmt, ast.Return):
            if stmt.value:
                return self._analyze_expression(stmt.value)
            return ComplexityRank.CONSTANT, "Constant return statement.", ComplexityRank.CONSTANT, "No auxiliary memory."
        else:
            return ComplexityRank.CONSTANT, "Constant statement.", ComplexityRank.CONSTANT, "Constant space."


    def _analyze_for_loop(
        self,
        loop: ast.For | ast.AsyncFor,
        current_func: Optional[str],
        all_funcs: Set[str],
    ) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        is_range, is_constant_range, range_size = self._inspect_range(loop.iter)

        if is_range:
            if is_constant_range:
                iter_rank = ComplexityRank.CONSTANT
                iter_desc = f"fixed range({range_size})"
            else:
                iter_rank = ComplexityRank.LINEAR
                iter_desc = "the input range"
        else:
            if isinstance(loop.iter, (ast.List, ast.Tuple, ast.Set)) and all(isinstance(e, ast.Constant) for e in loop.iter.elts):
                iter_rank = ComplexityRank.CONSTANT
                iter_desc = f"literal collection of {len(loop.iter.elts)} items"
            else:
                iter_rank = ComplexityRank.LINEAR
                iter_desc = "the input collection"

        body_t_rank, body_t_exp, body_s_rank, body_s_exp = self._analyze_block(loop.body, current_func, all_funcs)

        has_dynamic_growth = self._detect_growth_in_loop(loop.body)

        if iter_rank == ComplexityRank.CONSTANT:
            final_t_rank = body_t_rank
            final_t_exp = f"Loop runs a fixed constant number of iterations ({iter_desc})."
            final_s_rank = body_s_rank
            final_s_exp = body_s_exp
        else:
            if body_t_rank == ComplexityRank.CONSTANT:
                final_t_rank = ComplexityRank.LINEAR
                final_t_exp = f"The program iterates through {iter_desc} once in O(n) time."
            elif body_t_rank == ComplexityRank.LINEAR:
                final_t_rank = ComplexityRank.QUADRATIC
                final_t_exp = f"Nested loops detected: an outer loop iterating over {iter_desc} contains an inner O(n) loop, yielding O(n^2) time complexity."
            elif body_t_rank == ComplexityRank.LOGARITHMIC:
                final_t_rank = ComplexityRank.LINEARITHMIC
                final_t_exp = f"The program combines an outer O(n) loop with an inner O(log n) operation, yielding O(n log n) time complexity."
            elif body_t_rank == ComplexityRank.QUADRATIC:
                final_t_rank = ComplexityRank.CUBIC
                final_t_exp = f"Triple nested loops detected, yielding O(n^3) time complexity."
            else:
                final_t_rank = body_t_rank
                final_t_exp = f"Loop body contains {COMPLEXITY_NOTATIONS.get(body_t_rank, 'higher')} operations."

            if has_dynamic_growth or body_s_rank >= ComplexityRank.LINEAR:
                final_s_rank = ComplexityRank.LINEAR
                final_s_exp = "Data structure expands elements inside the loop, consuming O(n) auxiliary space."
            else:
                final_s_rank = body_s_rank
                final_s_exp = body_s_exp

        return final_t_rank, final_t_exp, final_s_rank, final_s_exp

    def _inspect_range(self, iter_node: ast.expr) -> Tuple[bool, bool, Optional[int]]:
        """Returns (is_range, is_constant, constant_size)."""
        if not isinstance(iter_node, ast.Call):
            return False, False, None

        if isinstance(iter_node.func, ast.Name) and iter_node.func.id == "range":
            args = iter_node.args
            if len(args) == 1:
                if isinstance(args[0], ast.Constant) and isinstance(args[0].value, int):
                    return True, True, args[0].value
                return True, False, None
            elif len(args) == 2:
                if (isinstance(args[0], ast.Constant) and isinstance(args[0].value, int) and
                        isinstance(args[1], ast.Constant) and isinstance(args[1].value, int)):
                    return True, True, abs(args[1].value - args[0].value)
                return True, False, None
            elif len(args) == 3:
                if (isinstance(args[0], ast.Constant) and isinstance(args[0].value, int) and
                        isinstance(args[1], ast.Constant) and isinstance(args[1].value, int) and
                        isinstance(args[2], ast.Constant) and isinstance(args[2].value, int)):
                    step = args[2].value
                    if step != 0:
                        return True, True, abs(args[1].value - args[0].value) // abs(step)
                return True, False, None
            return True, False, None

        return False, False, None

    def _analyze_while_loop(
        self,
        loop: ast.While,
        current_func: Optional[str],
        all_funcs: Set[str],
    ) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        is_binary_search = self._detect_binary_search_pattern(loop)
        if is_binary_search:
            body_t_rank, _, body_s_rank, _ = self._analyze_block(loop.body, current_func, all_funcs)
            s_rank = max(ComplexityRank.CONSTANT, body_s_rank)
            return (
                ComplexityRank.LOGARITHMIC,
                "Binary search pattern detected: search space is halved at each iteration (O(log n) time).",
                s_rank,
                "Iterative binary search uses O(1) auxiliary variables.",
            )

        is_linear_while = self._detect_linear_while_pattern(loop)
        if is_linear_while:
            body_t_rank, body_t_exp, body_s_rank, body_s_exp = self._analyze_block(loop.body, current_func, all_funcs)
            if body_t_rank == ComplexityRank.CONSTANT:
                t_rank = ComplexityRank.LINEAR
                t_exp = "While loop increments/decrements linearly over the variable range in O(n) time."
            elif body_t_rank == ComplexityRank.LINEAR:
                t_rank = ComplexityRank.QUADRATIC
                t_exp = "Nested loops in while loop structure yield O(n^2) time complexity."
            else:
                t_rank = body_t_rank
                t_exp = body_t_exp

            has_growth = self._detect_growth_in_loop(loop.body)
            s_rank = ComplexityRank.LINEAR if (has_growth or body_s_rank >= ComplexityRank.LINEAR) else body_s_rank
            s_exp = "Memory expands inside the while loop." if s_rank >= ComplexityRank.LINEAR else "Fixed scalar variables are used."
            return t_rank, t_exp, s_rank, s_exp

        if isinstance(loop.test, ast.Constant) and not loop.test.value:
            return ComplexityRank.CONSTANT, "Unreachable while condition.", ComplexityRank.CONSTANT, "No auxiliary memory."

        body_t_rank, body_t_exp, body_s_rank, body_s_exp = self._analyze_block(loop.body, current_func, all_funcs)
        has_break = any(isinstance(node, ast.Break) for node in ast.walk(loop))
        if has_break:
            return (
                ComplexityRank.LINEAR,
                "While loop with conditional break progression estimated at O(n) time.",
                body_s_rank,
                body_s_exp,
            )

        return (
            ComplexityRank.UNKNOWN,
            "While loop termination condition cannot be statically bounded without runtime input values.",
            ComplexityRank.UNKNOWN,
            "Space complexity depends on while loop execution path.",
        )

    def _detect_binary_search_pattern(self, loop: ast.While) -> bool:
        """Detects halving / binary search loop pattern: mid = (low + high)//2 or n //= 2."""
        has_mid_calc = False
        has_bound_update = False
        has_div_assign = False

        for node in ast.walk(loop):
            if isinstance(node, (ast.Assign, ast.AugAssign)):
                if isinstance(node, ast.Assign):
                    val = node.value
                    if isinstance(val, ast.BinOp):
                        if isinstance(val.op, (ast.FloorDiv, ast.Div, ast.RShift)):
                            has_mid_calc = True
                elif isinstance(node, ast.AugAssign):
                    if isinstance(node.op, (ast.FloorDiv, ast.Div, ast.RShift)):
                        has_div_assign = True

            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, (ast.Add, ast.Sub)):
                    has_bound_update = True

        return (has_mid_calc and has_bound_update) or has_div_assign

    def _detect_linear_while_pattern(self, loop: ast.While) -> bool:
        for node in ast.walk(loop):
            if isinstance(node, ast.AugAssign):
                if isinstance(node.op, (ast.Add, ast.Sub)):
                    return True
            elif isinstance(node, ast.Assign):
                if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, (ast.Add, ast.Sub)):
                    return True
        return False

    def _detect_growth_in_loop(self, body: List[ast.stmt]) -> bool:
        for stmt in body:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ("append", "extend", "insert", "add"):
                            return True
        return False


    def _analyze_if(
        self,
        node: ast.If,
        current_func: Optional[str],
        all_funcs: Set[str],
    ) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        t_then, exp_then, s_then, s_exp_then = self._analyze_block(node.body, current_func, all_funcs)
        t_else, exp_else, s_else, s_exp_else = self._analyze_block(node.orelse, current_func, all_funcs)

        max_t = max(t_then, t_else)
        t_exp = exp_then if t_then >= t_else else exp_else

        max_s = max(s_then, s_else)
        s_exp = s_exp_then if s_then >= s_else else s_exp_else

        return max_t, t_exp, max_s, s_exp

    def _analyze_try(
        self,
        node: ast.Try,
        current_func: Optional[str],
        all_funcs: Set[str],
    ) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        ranks = [self._analyze_block(node.body, current_func, all_funcs)]
        for handler in node.handlers:
            ranks.append(self._analyze_block(handler.body, current_func, all_funcs))
        if node.orelse:
            ranks.append(self._analyze_block(node.orelse, current_func, all_funcs))
        if node.finalbody:
            ranks.append(self._analyze_block(node.finalbody, current_func, all_funcs))

        max_t = max(r[0] for r in ranks)
        max_s = max(r[2] for r in ranks)
        t_exp = next(r[1] for r in ranks if r[0] == max_t)
        s_exp = next(r[3] for r in ranks if r[2] == max_s)

        return max_t, t_exp, max_s, s_exp


    def _analyze_assignment(self, stmt: ast.Assign | ast.AnnAssign | ast.AugAssign) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        val = getattr(stmt, "value", None)
        if val is None:
            return ComplexityRank.CONSTANT, "Declaration.", ComplexityRank.CONSTANT, "No allocation."
        return self._analyze_expression(val)

    def _analyze_expr_stmt(self, stmt: ast.Expr) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        return self._analyze_expression(stmt.value)

    def _analyze_expression(self, expr: ast.expr) -> Tuple[ComplexityRank, str, ComplexityRank, str]:
        if isinstance(expr, ast.ListComp):
            gen_count = len(expr.generators)
            if gen_count == 1:
                return (
                    ComplexityRank.LINEAR,
                    "List comprehension generates n elements in O(n) time.",
                    ComplexityRank.LINEAR,
                    "List comprehension allocates an array of size n in O(n) space.",
                )
            elif gen_count >= 2:
                return (
                    ComplexityRank.QUADRATIC,
                    "Nested list comprehension performs n^2 iterations.",
                    ComplexityRank.QUADRATIC,
                    "Nested list comprehension allocates an n x n data structure.",
                )

        if isinstance(expr, (ast.SetComp, ast.DictComp)):
            return (
                ComplexityRank.LINEAR,
                "Comprehension builds a collection of size n in O(n) time.",
                ComplexityRank.LINEAR,
                "Comprehension allocates auxiliary space proportional to n elements.",
            )

        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Mult):
            if isinstance(expr.left, ast.List) and not isinstance(expr.right, ast.Constant):
                return (
                    ComplexityRank.LINEAR,
                    "Array scaling allocation executes in O(n) time.",
                    ComplexityRank.LINEAR,
                    "Array of size n allocated in memory (O(n) auxiliary space).",
                )
            if isinstance(expr.right, ast.List) and not isinstance(expr.left, ast.Constant):
                return (
                    ComplexityRank.LINEAR,
                    "Array scaling allocation executes in O(n) time.",
                    ComplexityRank.LINEAR,
                    "Array of size n allocated in memory (O(n) auxiliary space).",
                )

        if isinstance(expr, ast.Call):
            func_name = ""
            if isinstance(expr.func, ast.Name):
                func_name = expr.func.id
            elif isinstance(expr.func, ast.Attribute):
                func_name = expr.func.attr

            if func_name in ("sorted", "sort"):
                return (
                    ComplexityRank.LINEARITHMIC,
                    "Sorting algorithm runs in O(n log n) comparison time.",
                    ComplexityRank.LINEAR,
                    "Sorting allocates auxiliary buffers (O(n) space).",
                )
            elif func_name in ("sum", "min", "max", "list", "set", "dict", "tuple"):
                if expr.args and not (isinstance(expr.args[0], (ast.List, ast.Tuple)) and all(isinstance(e, ast.Constant) for e in expr.args[0].elts)):
                    return (
                        ComplexityRank.LINEAR,
                        f"Built-in function '{func_name}' traverses the input collection in O(n) time.",
                        ComplexityRank.LINEAR if func_name in ("list", "set", "dict", "tuple") else ComplexityRank.CONSTANT,
                        f"Built-in '{func_name}' creates a new collection in O(n) space." if func_name in ("list", "set", "dict", "tuple") else "Scalar result stored in O(1) space.",
                    )

        return ComplexityRank.CONSTANT, "Constant time operation.", ComplexityRank.CONSTANT, "Constant auxiliary space."


    def _detect_recursion(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> Dict[str, Any]:
        func_name = func_node.name
        recursive_calls: List[ast.Call] = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    recursive_calls.append(node)

        if not recursive_calls:
            return {"is_recursive": False}

        call_count = len(recursive_calls)

        has_division = False
        mid_vars: Set[str] = set()

        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                val = node.value
                if isinstance(val, ast.BinOp) and isinstance(val.op, (ast.FloorDiv, ast.Div, ast.RShift)):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            mid_vars.add(target.id)
                    has_division = True

        has_subtraction = False
        for call in recursive_calls:
            for arg in call.args:
                for sub in ast.walk(arg):
                    if isinstance(sub, ast.BinOp):
                        if isinstance(sub.op, (ast.FloorDiv, ast.Div, ast.RShift)):
                            has_division = True
                        elif isinstance(sub.op, ast.Sub):
                            has_subtraction = True
                    elif isinstance(sub, ast.Name) and sub.id in mid_vars:
                        has_division = True

        is_concurrent = False
        for node in ast.walk(func_node):
            if isinstance(node, ast.BinOp):
                left_calls = [c for c in ast.walk(node.left) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == func_name]
                right_calls = [c for c in ast.walk(node.right) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == func_name]
                if left_calls and right_calls:
                    is_concurrent = True
            elif isinstance(node, (ast.List, ast.Tuple)):
                inner_calls = [c for elt in node.elts for c in ast.walk(elt) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == func_name]
                if len(inner_calls) >= 2:
                    is_concurrent = True

        effective_call_count = 2 if is_concurrent else (1 if call_count == 1 or not is_concurrent else call_count)

        if effective_call_count == 1:
            if has_division:
                return {
                    "is_recursive": True,
                    "time_rank": ComplexityRank.LOGARITHMIC,
                    "time_explanation": f"Divide-and-conquer recursion in '{func_name}': search space is halved at each recursive step, resulting in O(log n) time.",
                    "space_rank": ComplexityRank.LOGARITHMIC,
                    "space_explanation": "Recursion call stack reaches a maximum depth of O(log n).",
                }
            else:
                return {
                    "is_recursive": True,
                    "time_rank": ComplexityRank.LINEAR,
                    "time_explanation": f"Linear recursion in '{func_name}': function calls itself once per step reducing size linearly (O(n) time).",
                    "space_rank": ComplexityRank.LINEAR,
                    "space_explanation": "Call stack depth reaches O(n) auxiliary space.",
                }

        elif effective_call_count >= 2:
            if has_division:
                return {
                    "is_recursive": True,
                    "time_rank": ComplexityRank.LINEARITHMIC,
                    "time_explanation": f"Divide-and-conquer recursion branching into 2 subproblems with halving, resulting in O(n log n) time complexity.",
                    "space_rank": ComplexityRank.LINEAR,
                    "space_explanation": "Recursion call stack frames consume O(n) auxiliary space.",
                }
            else:
                return {
                    "is_recursive": True,
                    "time_rank": ComplexityRank.EXPONENTIAL,
                    "time_explanation": f"Exponential recursion in '{func_name}': multiple concurrent recursive calls reduce problem size linearly (O(2^n) time).",
                    "space_rank": ComplexityRank.LINEAR,
                    "space_explanation": "Maximum recursion stack depth reaches O(n) frames.",
                }

        return {
            "is_recursive": True,
            "time_rank": ComplexityRank.LINEAR,
            "time_explanation": f"Recursive function '{func_name}' executes in estimated O(n) time.",
            "space_rank": ComplexityRank.LINEAR,
            "space_explanation": "Call stack frames consume O(n) auxiliary space.",
        }


def analyze_complexity(source_code: str) -> ComplexityResult:
    """
    Convenience function to analyze Python source code complexity.
    """
    analyzer = ComplexityAnalyzer()
    return analyzer.analyze(source_code)
