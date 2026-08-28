from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Set, Type

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
from .exceptions import UnsupportedIRNodeError


class BaseCodeGenerator(ABC):

    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size
        self._indent_level = 0
        self._required_helpers: Set[str] = set()

    def indent(self) -> None:
        self._indent_level += 1

    def dedent(self) -> None:
        self._indent_level = max(0, self._indent_level - 1)

    def get_indent(self) -> str:
        return " " * (self._indent_level * self.indent_size)

    def require_runtime_helper(self, helper_name: str) -> None:
        self._required_helpers.add(helper_name)

    def supports_feature(self, feature_name: str) -> bool:
        return True

    def generate(self, node: Optional[IRNode]) -> str:
        if node is None:
            return ""

        handler = self._get_dispatch_handler(node.__class__)
        if handler is not None:
            return handler(node)

        return self.generic_generate(node)

    def _get_dispatch_handler(self, node_class: Type[IRNode]) -> Optional[Callable[[Any], str]]:
        dispatch_map: Dict[Type[IRNode], Callable[[Any], str]] = {
            IRProgram: self.generate_program,
            IRImport: self.generate_import,
            IRFunction: self.generate_function,
            IRClass: self.generate_class,
            IRVariable: self.generate_variable,
            IRConstant: self.generate_constant,
            IRName: self.generate_name,
            IRAssignment: self.generate_assignment,
            IRTupleAssignment: self.generate_tuple_assignment,
            IRReturn: self.generate_return,
            IRExpressionStatement: self.generate_expression_statement,
            IRIf: self.generate_if,
            IRFor: self.generate_for,
            IRWhile: self.generate_while,
            IRBreak: self.generate_break,
            IRContinue: self.generate_continue,
            IRBinaryOperation: self.generate_binary_operation,
            IRUnaryOperation: self.generate_unary_operation,
            IRChainedComparison: self.generate_chained_comparison,
            IRConditionalExpression: self.generate_conditional_expression,
            IRLambda: self.generate_lambda,
            IRFunctionCall: self.generate_function_call,
            IRList: self.generate_list,
            IRTuple: self.generate_tuple,
            IRSet: self.generate_set,
            IRDict: self.generate_dict,
            IRSubscript: self.generate_subscript,
            IRSlice: self.generate_slice,
            IRAttribute: self.generate_attribute,
            IRTry: self.generate_try,
            IRExcept: self.generate_except,
            IRRaise: self.generate_raise,
            IRAssert: self.generate_assert,
            IRYield: self.generate_yield,
            IRGeneratorExpression: self.generate_generator_expression,
            IRStarred: self.generate_starred,
            IRIsInstance: self.generate_isinstance,
            IRListComprehension: self.generate_list_comprehension,
            IRSetComprehension: self.generate_set_comprehension,
            IRDictComprehension: self.generate_dict_comprehension,
        }
        return dispatch_map.get(node_class)

    def generic_generate(self, node: IRNode) -> str:
        raise UnsupportedIRNodeError(node_type=node.__class__.__name__)

    @abstractmethod
    def generate_program(self, node: IRProgram) -> str:
        pass

    @abstractmethod
    def generate_import(self, node: IRImport) -> str:
        pass

    @abstractmethod
    def generate_function(self, node: IRFunction) -> str:
        pass

    @abstractmethod
    def generate_class(self, node: IRClass) -> str:
        pass

    @abstractmethod
    def generate_variable(self, node: IRVariable) -> str:
        pass

    @abstractmethod
    def generate_constant(self, node: IRConstant) -> str:
        pass

    @abstractmethod
    def generate_name(self, node: IRName) -> str:
        pass

    @abstractmethod
    def generate_assignment(self, node: IRAssignment) -> str:
        pass

    def generate_tuple_assignment(self, node: IRTupleAssignment) -> str:
        return self.generic_generate(node)

    @abstractmethod
    def generate_return(self, node: IRReturn) -> str:
        pass

    @abstractmethod
    def generate_expression_statement(self, node: IRExpressionStatement) -> str:
        pass

    @abstractmethod
    def generate_if(self, node: IRIf) -> str:
        pass

    @abstractmethod
    def generate_for(self, node: IRFor) -> str:
        pass

    @abstractmethod
    def generate_while(self, node: IRWhile) -> str:
        pass

    @abstractmethod
    def generate_binary_operation(self, node: IRBinaryOperation) -> str:
        pass

    @abstractmethod
    def generate_unary_operation(self, node: IRUnaryOperation) -> str:
        pass

    def generate_conditional_expression(self, node: IRConditionalExpression) -> str:
        return self.generic_generate(node)

    @abstractmethod
    def generate_function_call(self, node: IRFunctionCall) -> str:
        pass

    def generate_list(self, node: IRList) -> str:
        return self.generic_generate(node)

    def generate_tuple(self, node: IRTuple) -> str:
        return self.generic_generate(node)

    def generate_dict(self, node: IRDict) -> str:
        return self.generic_generate(node)

    def generate_subscript(self, node: IRSubscript) -> str:
        return self.generic_generate(node)

    def generate_slice(self, node: IRSlice) -> str:
        return self.generic_generate(node)

    def generate_attribute(self, node: IRAttribute) -> str:
        return self.generic_generate(node)

    def generate_try(self, node: IRTry) -> str:
        return self.generic_generate(node)

    def generate_except(self, node: IRExcept) -> str:
        return self.generic_generate(node)

    def generate_raise(self, node: IRRaise) -> str:
        return self.generic_generate(node)

    def generate_break(self, node: IRBreak) -> str:
        return "break;"

    def generate_continue(self, node: IRContinue) -> str:
        return "continue;"

    def generate_chained_comparison(self, node: IRChainedComparison) -> str:
        return self.generic_generate(node)

    def generate_lambda(self, node: IRLambda) -> str:
        return self.generic_generate(node)

    def generate_set(self, node: IRSet) -> str:
        return self.generic_generate(node)

    def generate_set_comprehension(self, node: IRSetComprehension) -> str:
        return self.generic_generate(node)

    def generate_dict_comprehension(self, node: IRDictComprehension) -> str:
        return self.generic_generate(node)

    def generate_list_comprehension(self, node: IRListComprehension) -> str:
        return self.generic_generate(node)

    def generate_assert(self, node: IRAssert) -> str:
        return self.generic_generate(node)

    def generate_yield(self, node: IRYield) -> str:
        return self.generic_generate(node)

    def generate_generator_expression(self, node: IRGeneratorExpression) -> str:
        return self.generic_generate(node)

    def generate_starred(self, node: IRStarred) -> str:
        return self.generic_generate(node)

    def generate_isinstance(self, node: IRIsInstance) -> str:
        return self.generic_generate(node)
