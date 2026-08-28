"""
Rosetta AI - Intermediate Representation (IR) Builder
------------------------------------------------------
Constructs a language-independent IR from a Python Abstract Syntax Tree (AST).
"""

import ast
from typing import Any, Dict, List, Optional, Type, Union

from .nodes import (
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

BINARY_OPERATOR_MAP: Dict[Type[ast.operator], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.BitAnd: "&",
    ast.MatMult: "@",
}

COMPARISON_OPERATOR_MAP: Dict[Type[ast.cmpop], str] = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in",
}

UNARY_OPERATOR_MAP: Dict[Type[ast.unaryop], str] = {
    ast.UAdd: "+",
    ast.USub: "-",
    ast.Not: "not",
    ast.Invert: "~",
}


class IRBuilder:
    """
    Transforms Python AST trees into Rosetta AI Intermediate Representation (IR).
    """

    def build_from_source(self, source_code: str) -> IRProgram:
        """Parses Python source code and builds the IRProgram."""
        if not source_code or not source_code.strip():
            return IRProgram()
        tree = ast.parse(source_code)
        return self.build_from_ast(tree)

    def build_from_ast(self, tree: ast.AST) -> IRProgram:
        """Builds an IRProgram directly from an existing ast.AST node."""
        program = IRProgram()

        if isinstance(tree, ast.Module):
            for stmt in tree.body:
                ir_stmt = self.transform_statement(stmt)
                if ir_stmt is not None:
                    program.statements.append(ir_stmt)

                    if isinstance(ir_stmt, IRImport):
                        program.imports.append(ir_stmt)
                    elif isinstance(ir_stmt, IRFunction):
                        program.functions.append(ir_stmt)
                    elif isinstance(ir_stmt, IRClass):
                        program.classes.append(ir_stmt)
        else:
            single_stmt = self.transform_statement(tree)
            if single_stmt:
                program.statements.append(single_stmt)

        return program

    def transform_statement(self, node: ast.AST) -> Optional[IRNode]:
        """Dispatches an AST statement node to its corresponding IR transformer."""
        if isinstance(node, ast.Import):
            return self._transform_import(node)
        elif isinstance(node, ast.ImportFrom):
            return self._transform_import_from(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._transform_function(node)
        elif isinstance(node, ast.ClassDef):
            return self._transform_class(node)
        elif isinstance(node, ast.Assign):
            return self._transform_assign(node)
        elif isinstance(node, ast.AnnAssign):
            return self._transform_ann_assign(node)
        elif isinstance(node, ast.AugAssign):
            return self._transform_aug_assign(node)
        elif isinstance(node, ast.If):
            return self._transform_if(node)
        elif isinstance(node, ast.For):
            return self._transform_for(node)
        elif isinstance(node, ast.While):
            return self._transform_while(node)
        elif isinstance(node, ast.Break):
            return IRBreak()
        elif isinstance(node, ast.Continue):
            return IRContinue()
        elif isinstance(node, ast.Assert):
            return IRAssert(
                condition=self.transform_expression(node.test),
                message=self.transform_expression(node.msg) if node.msg else None,
            )
        elif isinstance(node, ast.Return):
            return self._transform_return(node)
        elif isinstance(node, ast.Try):
            return self._transform_try(node)
        elif isinstance(node, ast.Raise):
            return self._transform_raise(node)
        elif isinstance(node, ast.Expr):
            return IRExpressionStatement(expression=self.transform_expression(node.value))
        elif isinstance(node, ast.Pass):
            return IRExpressionStatement(expression=IRName(name="pass"))
        else:
            expr = self.transform_expression(node)
            return IRExpressionStatement(expression=expr) if expr else None

    def _transform_import(self, node: ast.Import) -> IRImport:
        names = [
            f"{alias.name} as {alias.asname}" if alias.asname else alias.name
            for alias in node.names
        ]
        module_name = node.names[0].name if len(node.names) == 1 and not node.names[0].asname else None
        return IRImport(
            module=module_name,
            names=names,
            is_from_import=False,
        )

    def _transform_import_from(self, node: ast.ImportFrom) -> IRImport:
        names = [
            f"{alias.name} as {alias.asname}" if alias.asname else alias.name
            for alias in node.names
        ]
        return IRImport(
            module=node.module,
            names=names,
            is_from_import=True,
        )

    def _transform_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> IRFunction:
        params = [arg.arg for arg in node.args.args]
        posonly_params = [arg.arg for arg in getattr(node.args, "posonlyargs", [])]
        kwonly_params = [arg.arg for arg in getattr(node.args, "kwonlyargs", [])]
        vararg = node.args.vararg.arg if node.args.vararg else None
        kwarg = node.args.kwarg.arg if node.args.kwarg else None

        param_types = {}
        all_args = list(getattr(node.args, "posonlyargs", [])) + node.args.args + list(getattr(node.args, "kwonlyargs", []))
        if node.args.vararg:
            all_args.append(node.args.vararg)
        if node.args.kwarg:
            all_args.append(node.args.kwarg)

        for arg in all_args:
            if arg.annotation:
                param_types[arg.arg] = ast.unparse(arg.annotation)

        default_values = {}
        if node.args.defaults:
            offset = len(node.args.args) - len(node.args.defaults)
            for i, def_node in enumerate(node.args.defaults):
                param_name = node.args.args[offset + i].arg
                def_ir = self.transform_expression(def_node)
                if def_ir:
                    default_values[param_name] = def_ir

        if kwonly_params and getattr(node.args, "kw_defaults", []):
            for kw_name, def_node in zip(kwonly_params, node.args.kw_defaults):
                if def_node:
                    def_ir = self.transform_expression(def_node)
                    if def_ir:
                        default_values[kw_name] = def_ir

        if vararg and f"*{vararg}" not in params:
            params.append(f"*{vararg}")
        if kwarg and f"**{kwarg}" not in params:
            params.append(f"**{kwarg}")

        body_nodes: List[IRNode] = []
        for stmt in node.body:
            transformed = self.transform_statement(stmt)
            if transformed:
                body_nodes.append(transformed)

        return_type = ast.unparse(node.returns) if node.returns else None

        return IRFunction(
            name=node.name,
            parameters=params,
            posonly_parameters=posonly_params,
            kwonly_parameters=kwonly_params,
            vararg=vararg,
            kwarg=kwarg,
            parameter_types=param_types,
            default_values=default_values,
            body=body_nodes,
            return_type=return_type,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            docstring=ast.get_docstring(node),
        )

    def _transform_class(self, node: ast.ClassDef) -> IRClass:
        bases = [ast.unparse(base) for base in node.bases]
        methods: List[IRFunction] = []
        body_nodes: List[IRNode] = []

        for stmt in node.body:
            transformed = self.transform_statement(stmt)
            if transformed:
                body_nodes.append(transformed)
                if isinstance(transformed, IRFunction):
                    methods.append(transformed)

        return IRClass(
            name=node.name,
            bases=bases,
            methods=methods,
            body=body_nodes,
            docstring=ast.get_docstring(node),
        )

    def _transform_assign(self, node: ast.Assign) -> Union[IRAssignment, IRTupleAssignment]:
        if node.targets and isinstance(node.targets[0], (ast.Tuple, ast.List)):
            targets = [ast.unparse(elt) for elt in node.targets[0].elts]
            value_ir = self.transform_expression(node.value)
            return IRTupleAssignment(
                targets=targets,
                value=value_ir,
            )

        target_name = ast.unparse(node.targets[0]) if node.targets else ""
        value_ir = self.transform_expression(node.value)
        return IRAssignment(
            target=target_name,
            value=value_ir,
        )

    def _transform_ann_assign(self, node: ast.AnnAssign) -> IRAssignment:
        target_name = ast.unparse(node.target)
        value_ir = self.transform_expression(node.value) if node.value else None
        type_str = ast.unparse(node.annotation)
        return IRAssignment(
            target=target_name,
            value=value_ir,
            var_type=type_str,
        )

    def _transform_aug_assign(self, node: ast.AugAssign) -> IRAssignment:
        target_name = ast.unparse(node.target)
        op = BINARY_OPERATOR_MAP.get(type(node.op), node.op.__class__.__name__)
        right_ir = self.transform_expression(node.value)
        left_ir = IRName(name=target_name)

        return IRAssignment(
            target=target_name,
            value=IRBinaryOperation(left=left_ir, operator=op, right=right_ir),
        )

    def _transform_if(self, node: ast.If) -> IRIf:
        cond_ir = self.transform_expression(node.test)
        then_body = [self.transform_statement(s) for s in node.body]
        else_body = [self.transform_statement(s) for s in node.orelse]

        return IRIf(
            condition=cond_ir,
            then_body=[s for s in then_body if s],
            else_body=[s for s in else_body if s],
        )

    def _transform_for(self, node: ast.For) -> IRFor:
        var_name = ast.unparse(node.target)
        iter_ir = self.transform_expression(node.iter)
        body = [self.transform_statement(s) for s in node.body]
        else_body = [self.transform_statement(s) for s in node.orelse]

        return IRFor(
            variable=var_name,
            iterable=iter_ir,
            body=[s for s in body if s],
            else_body=[s for s in else_body if s],
        )

    def _transform_while(self, node: ast.While) -> IRWhile:
        cond_ir = self.transform_expression(node.test)
        body = [self.transform_statement(s) for s in node.body]
        else_body = [self.transform_statement(s) for s in node.orelse]

        return IRWhile(
            condition=cond_ir,
            body=[s for s in body if s],
            else_body=[s for s in else_body if s],
        )

    def _transform_return(self, node: ast.Return) -> IRReturn:
        val_ir = self.transform_expression(node.value) if node.value else None
        return IRReturn(value=val_ir)

    def _transform_try(self, node: ast.Try) -> IRTry:
        body = [self.transform_statement(s) for s in node.body]
        handlers: List[IRExcept] = []
        for h in node.handlers:
            exc_type = ast.unparse(h.type) if h.type else None
            h_body = [self.transform_statement(s) for s in h.body]
            handlers.append(
                IRExcept(
                    exception_type=exc_type,
                    alias=h.name,
                    body=[s for s in h_body if s],
                )
            )
        else_body = [self.transform_statement(s) for s in node.orelse]
        finally_body = [self.transform_statement(s) for s in node.finalbody]
        return IRTry(
            body=[s for s in body if s],
            handlers=handlers,
            else_body=[s for s in else_body if s],
            finally_body=[s for s in finally_body if s],
        )

    def _transform_raise(self, node: ast.Raise) -> IRRaise:
        exc_ir = self.transform_expression(node.exc) if node.exc else None
        return IRRaise(exception=exc_ir)

    def _transform_list_comp(self, node: ast.ListComp) -> IRListComprehension:
        gen = node.generators[0]
        target = ast.unparse(gen.target)
        iter_ir = self.transform_expression(gen.iter)
        cond_ir = self.transform_expression(gen.ifs[0]) if gen.ifs else None
        elt_ir = self.transform_expression(node.elt)
        return IRListComprehension(
            element=elt_ir,
            variable=target,
            iterable=iter_ir,
            condition=cond_ir,
        )

    def _transform_set_comp(self, node: ast.SetComp) -> IRSetComprehension:
        gen = node.generators[0]
        target = ast.unparse(gen.target)
        iter_ir = self.transform_expression(gen.iter)
        cond_ir = self.transform_expression(gen.ifs[0]) if gen.ifs else None
        elt_ir = self.transform_expression(node.elt)
        return IRSetComprehension(
            element=elt_ir,
            variable=target,
            iterable=iter_ir,
            condition=cond_ir,
        )

    def _transform_dict_comp(self, node: ast.DictComp) -> IRDictComprehension:
        gen = node.generators[0]
        target = ast.unparse(gen.target)
        iter_ir = self.transform_expression(gen.iter)
        cond_ir = self.transform_expression(gen.ifs[0]) if gen.ifs else None
        key_ir = self.transform_expression(node.key)
        val_ir = self.transform_expression(node.value)
        return IRDictComprehension(
            key=key_ir,
            value=val_ir,
            variable=target,
            iterable=iter_ir,
            condition=cond_ir,
        )

    def _transform_gen_exp(self, node: ast.GeneratorExp) -> IRGeneratorExpression:
        gen = node.generators[0]
        target = ast.unparse(gen.target)
        iter_ir = self.transform_expression(gen.iter)
        cond_ir = self.transform_expression(gen.ifs[0]) if gen.ifs else None
        elt_ir = self.transform_expression(node.elt)
        return IRGeneratorExpression(
            element=elt_ir,
            variable=target,
            iterable=iter_ir,
            condition=cond_ir,
        )

    def transform_expression(self, node: Optional[ast.AST]) -> Optional[IRNode]:
        """Dispatches an AST expression node to its corresponding IR node."""
        if node is None:
            return None

        if isinstance(node, ast.BinOp):
            op = BINARY_OPERATOR_MAP.get(type(node.op), node.op.__class__.__name__)
            return IRBinaryOperation(
                left=self.transform_expression(node.left),
                operator=op,
                right=self.transform_expression(node.right),
            )

        elif isinstance(node, ast.Compare):
            if len(node.ops) > 1:
                operands = [self.transform_expression(node.left)] + [
                    self.transform_expression(c) for c in node.comparators
                ]
                operators = [
                    COMPARISON_OPERATOR_MAP.get(type(op), op.__class__.__name__)
                    for op in node.ops
                ]
                return IRChainedComparison(
                    operands=[o for o in operands if o is not None],
                    operators=operators,
                )
            else:
                left = self.transform_expression(node.left)
                op_str = COMPARISON_OPERATOR_MAP.get(type(node.ops[0]), node.ops[0].__class__.__name__)
                right = self.transform_expression(node.comparators[0])
                return IRBinaryOperation(left=left, operator=op_str, right=right)

        elif isinstance(node, ast.BoolOp):
            op_str = "and" if isinstance(node.op, ast.And) else "or"
            values_ir = [self.transform_expression(v) for v in node.values]
            result = values_ir[0]
            for next_val in values_ir[1:]:
                result = IRBinaryOperation(left=result, operator=op_str, right=next_val)
            return result

        elif isinstance(node, ast.UnaryOp):
            op = UNARY_OPERATOR_MAP.get(type(node.op), node.op.__class__.__name__)
            return IRUnaryOperation(
                operator=op,
                operand=self.transform_expression(node.operand),
            )

        elif isinstance(node, ast.IfExp):
            return IRConditionalExpression(
                condition=self.transform_expression(node.test),
                then_expression=self.transform_expression(node.body),
                else_expression=self.transform_expression(node.orelse),
            )

        elif isinstance(node, ast.Lambda):
            params = [arg.arg for arg in node.args.args]
            return IRLambda(
                parameters=params,
                body=self.transform_expression(node.body),
            )

        elif isinstance(node, (ast.Yield, ast.YieldFrom)):
            return IRYield(value=self.transform_expression(node.value) if node.value else None)

        elif isinstance(node, ast.GeneratorExp):
            return self._transform_gen_exp(node)

        elif isinstance(node, ast.Call):
            func_name = ast.unparse(node.func)
            if func_name == "isinstance" and len(node.args) == 2:
                return IRIsInstance(
                    expression=self.transform_expression(node.args[0]),
                    type_name=ast.unparse(node.args[1]),
                )
            args = []
            for arg in node.args:
                if isinstance(arg, ast.Starred):
                    args.append(IRStarred(value=self.transform_expression(arg.value), is_double=False))
                else:
                    args.append(self.transform_expression(arg))
            keywords = {}
            for kw in node.keywords:
                if kw.arg is None:
                    args.append(IRStarred(value=self.transform_expression(kw.value), is_double=True))
                else:
                    kw_ir = self.transform_expression(kw.value)
                    if kw_ir:
                        keywords[kw.arg] = kw_ir
            return IRFunctionCall(
                name=func_name,
                arguments=[a for a in args if a is not None],
                keywords=keywords,
            )

        elif isinstance(node, ast.Constant):
            data_type = type(node.value).__name__
            return IRConstant(
                value=node.value,
                data_type=data_type,
            )

        elif isinstance(node, ast.Name):
            return IRName(name=node.id)

        elif isinstance(node, ast.List):
            elts = [self.transform_expression(el) for el in node.elts]
            return IRList(elements=[e for e in elts if e is not None])

        elif isinstance(node, ast.Tuple):
            elts = [self.transform_expression(el) for el in node.elts]
            return IRTuple(elements=[e for e in elts if e is not None])

        elif isinstance(node, ast.Set):
            elts = [self.transform_expression(el) for el in node.elts]
            return IRSet(elements=[e for e in elts if e is not None])

        elif isinstance(node, ast.Dict):
            keys = [self.transform_expression(k) for k in node.keys if k is not None]
            values = [self.transform_expression(v) for v in node.values]
            return IRDict(
                keys=[k for k in keys if k is not None],
                values=[v for v in values if v is not None],
            )

        elif isinstance(node, ast.Subscript):
            value_ir = self.transform_expression(node.value)
            slice_ir = self.transform_slice(node.slice)
            return IRSubscript(value=value_ir, slice=slice_ir)

        elif isinstance(node, ast.Slice):
            return self.transform_slice(node)

        elif isinstance(node, ast.Attribute):
            value_ir = self.transform_expression(node.value)
            return IRAttribute(value=value_ir, attribute=node.attr)

        elif isinstance(node, ast.ListComp):
            return self._transform_list_comp(node)

        elif isinstance(node, ast.SetComp):
            return self._transform_set_comp(node)

        elif isinstance(node, ast.DictComp):
            return self._transform_dict_comp(node)

        else:
            return IRName(name=ast.unparse(node))

    def transform_slice(self, node: Optional[ast.AST]) -> Optional[IRNode]:
        """Transforms a slice AST node or slice index into IR."""
        if node is None:
            return None
        if isinstance(node, ast.Slice):
            lower_ir = self.transform_expression(node.lower) if node.lower is not None else None
            upper_ir = self.transform_expression(node.upper) if node.upper is not None else None
            step_ir = self.transform_expression(node.step) if node.step is not None else None
            return IRSlice(lower=lower_ir, upper=upper_ir, step=step_ir)
        return self.transform_expression(node)


def build_ir(source_or_ast: Union[str, ast.AST]) -> IRProgram:
    """
    Convenience function to convert Python source code or an AST tree into an IRProgram.
    """
    builder = IRBuilder()
    if isinstance(source_or_ast, str):
        return builder.build_from_source(source_or_ast)
    return builder.build_from_ast(source_or_ast)
