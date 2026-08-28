"""
Rosetta AI - Intermediate Representation (IR) Nodes
---------------------------------------------------
Language-agnostic AST/IR node definitions for representing core programming
constructs across languages (functions, classes, control flows, expressions).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IRNode:
    """Base class for all Intermediate Representation (IR) nodes."""

    def to_dict(self) -> Dict[str, Any]:
        """Recursively serialize the IR node and all children into a JSON-compatible dictionary."""
        result: Dict[str, Any] = {"node_type": self.__class__.__name__}
        for k, v in self.__dict__.items():
            result[k] = self._serialize_value(v)
        return result

    @classmethod
    def _serialize_value(cls, val: Any) -> Any:
        if isinstance(val, IRNode):
            return val.to_dict()
        elif isinstance(val, list):
            return [cls._serialize_value(item) for item in val]
        elif isinstance(val, dict):
            return {k: cls._serialize_value(v) for k, v in val.items()}
        else:
            return val


@dataclass
class IRImport(IRNode):
    """Represents an import statement."""
    module: Optional[str] = None
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_from_import: bool = False


@dataclass
class IRFunction(IRNode):
    """Represents a function or method definition."""
    name: str = ""
    parameters: List[str] = field(default_factory=list)
    posonly_parameters: List[str] = field(default_factory=list)
    kwonly_parameters: List[str] = field(default_factory=list)
    vararg: Optional[str] = None
    kwarg: Optional[str] = None
    parameter_types: Dict[str, str] = field(default_factory=dict)
    default_values: Dict[str, "IRNode"] = field(default_factory=dict)
    body: List[IRNode] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False
    docstring: Optional[str] = None


@dataclass
class IRClass(IRNode):
    """Represents a class definition."""
    name: str = ""
    bases: List[str] = field(default_factory=list)
    methods: List[IRFunction] = field(default_factory=list)
    body: List[IRNode] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class IRProgram(IRNode):
    """Root container representing the entire program / translation unit."""
    imports: List[IRImport] = field(default_factory=list)
    functions: List[IRFunction] = field(default_factory=list)
    classes: List[IRClass] = field(default_factory=list)
    statements: List[IRNode] = field(default_factory=list)


@dataclass
class IRVariable(IRNode):
    """Represents a variable reference or declaration."""
    name: str = ""
    var_type: Optional[str] = None


@dataclass
class IRConstant(IRNode):
    """Represents literal constant values (numbers, strings, booleans, None)."""
    value: Any = None
    data_type: str = ""


@dataclass
class IRName(IRNode):
    """Represents an identifier/variable reference within an expression."""
    name: str = ""


@dataclass
class IRAssignment(IRNode):
    """Represents variable assignments (e.g., target = value)."""
    target: str = ""
    value: Optional[IRNode] = None
    var_type: Optional[str] = None


@dataclass
class IRTupleAssignment(IRNode):
    """Represents multiple assignment / tuple unpacking (e.g., a, b = 1, 2 or x, y = point)."""
    targets: List[str] = field(default_factory=list)
    value: Optional[IRNode] = None


@dataclass
class IRReturn(IRNode):
    """Represents a function return statement."""
    value: Optional[IRNode] = None


@dataclass
class IRExpressionStatement(IRNode):
    """Represents a standalone expression executed as a statement (e.g. print(x))."""
    expression: Optional[IRNode] = None


@dataclass
class IRIf(IRNode):
    """Represents conditional if / else branching."""
    condition: Optional[IRNode] = None
    then_body: List[IRNode] = field(default_factory=list)
    else_body: List[IRNode] = field(default_factory=list)


@dataclass
class IRFor(IRNode):
    """Represents for-in iteration loops."""
    variable: str = ""
    iterable: Optional[IRNode] = None
    body: List[IRNode] = field(default_factory=list)
    else_body: List[IRNode] = field(default_factory=list)


@dataclass
class IRWhile(IRNode):
    """Represents while condition loops."""
    condition: Optional[IRNode] = None
    body: List[IRNode] = field(default_factory=list)
    else_body: List[IRNode] = field(default_factory=list)


@dataclass
class IRBreak(IRNode):
    """Represents a loop break statement."""
    pass


@dataclass
class IRContinue(IRNode):
    """Represents a loop continue statement."""
    pass


@dataclass
class IRBinaryOperation(IRNode):
    """Represents binary operations (+, -, *, /, >, <, ==, in, not in, etc.)."""
    left: Optional[IRNode] = None
    operator: str = ""
    right: Optional[IRNode] = None


@dataclass
class IRUnaryOperation(IRNode):
    """Represents unary operations (-, +, not, ~)."""
    operator: str = ""
    operand: Optional[IRNode] = None


@dataclass
class IRChainedComparison(IRNode):
    """Represents chained comparison operations (e.g. 1 < x < 10 or a <= b <= c)."""
    operands: List[IRNode] = field(default_factory=list)
    operators: List[str] = field(default_factory=list)


@dataclass
class IRConditionalExpression(IRNode):
    """Represents a ternary conditional expression (value_if_true if condition else value_if_false)."""
    condition: Optional[IRNode] = None
    then_expression: Optional[IRNode] = None
    else_expression: Optional[IRNode] = None


@dataclass
class IRLambda(IRNode):
    """Represents an anonymous lambda function (e.g. lambda x: x * 2)."""
    parameters: List[str] = field(default_factory=list)
    body: Optional[IRNode] = None


@dataclass
class IRFunctionCall(IRNode):
    """Represents function invocation."""
    name: str = ""
    arguments: List[IRNode] = field(default_factory=list)
    keywords: Dict[str, IRNode] = field(default_factory=dict)


@dataclass
class IRList(IRNode):
    """Represents a list literal (e.g. [1, 2, 3])."""
    elements: List[IRNode] = field(default_factory=list)


@dataclass
class IRTuple(IRNode):
    """Represents a tuple literal (e.g. (1, 2, 3) or a, b)."""
    elements: List[IRNode] = field(default_factory=list)


@dataclass
class IRSet(IRNode):
    """Represents a set literal (e.g. {1, 2, 3})."""
    elements: List[IRNode] = field(default_factory=list)


@dataclass
class IRDict(IRNode):
    """Represents a dictionary literal (e.g. {'a': 1, 'b': 2})."""
    keys: List[IRNode] = field(default_factory=list)
    values: List[IRNode] = field(default_factory=list)


@dataclass
class IRSubscript(IRNode):
    """Represents indexing into a collection or string (e.g. items[0], data['key'])."""
    value: Optional[IRNode] = None
    slice: Optional[IRNode] = None


@dataclass
class IRSlice(IRNode):
    """Represents a slice operation (e.g. [lower:upper:step])."""
    lower: Optional[IRNode] = None
    upper: Optional[IRNode] = None
    step: Optional[IRNode] = None


@dataclass
class IRAttribute(IRNode):
    """Represents attribute access (e.g. obj.property)."""
    value: Optional[IRNode] = None
    attribute: str = ""


@dataclass
class IRAssert(IRNode):
    condition: Optional[IRNode] = None
    message: Optional[IRNode] = None


@dataclass
class IRYield(IRNode):
    value: Optional[IRNode] = None


@dataclass
class IRGeneratorExpression(IRNode):
    element: Optional[IRNode] = None
    variable: str = ""
    iterable: Optional[IRNode] = None
    condition: Optional[IRNode] = None


@dataclass
class IRStarred(IRNode):
    value: Optional[IRNode] = None
    is_double: bool = False


@dataclass
class IRIsInstance(IRNode):
    expression: Optional[IRNode] = None
    type_name: str = ""


@dataclass
class IRExcept(IRNode):
    exception_type: Optional[str] = None
    alias: Optional[str] = None
    body: List[IRNode] = field(default_factory=list)


@dataclass
class IRTry(IRNode):
    body: List[IRNode] = field(default_factory=list)
    handlers: List[IRExcept] = field(default_factory=list)
    else_body: List[IRNode] = field(default_factory=list)
    finally_body: List[IRNode] = field(default_factory=list)


@dataclass
class IRRaise(IRNode):
    exception: Optional[IRNode] = None


@dataclass
class IRListComprehension(IRNode):
    element: Optional[IRNode] = None
    variable: str = ""
    iterable: Optional[IRNode] = None
    condition: Optional[IRNode] = None


@dataclass
class IRSetComprehension(IRNode):
    element: Optional[IRNode] = None
    variable: str = ""
    iterable: Optional[IRNode] = None
    condition: Optional[IRNode] = None


@dataclass
class IRDictComprehension(IRNode):
    key: Optional[IRNode] = None
    value: Optional[IRNode] = None
    variable: str = ""
    iterable: Optional[IRNode] = None
    condition: Optional[IRNode] = None
