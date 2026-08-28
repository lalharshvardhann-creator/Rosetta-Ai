import sys
from pathlib import Path
import unittest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ir.nodes import (
    IRAssignment,
    IRBinaryOperation,
    IRClass,
    IRConstant,
    IRExpressionStatement,
    IRFor,
    IRFunction,
    IRFunctionCall,
    IRIf,
    IRImport,
    IRName,
    IRNode,
    IRProgram,
    IRReturn,
    IRUnaryOperation,
    IRVariable,
    IRWhile,
)
from app.translation import (
    BaseCodeGenerator,
    GeneratorNotFoundError,
    TranslationEngine,
    UnsupportedIRNodeError,
)


class DummyPseudocodeGenerator(BaseCodeGenerator):

    def generate_program(self, node: IRProgram) -> str:
        lines = []
        for imp in node.imports:
            lines.append(self.generate(imp))
        for cls in node.classes:
            lines.append(self.generate(cls))
        for func in node.functions:
            lines.append(self.generate(func))
        for stmt in node.statements:
            if stmt not in node.imports and stmt not in node.classes and stmt not in node.functions:
                lines.append(self.generate(stmt))
        return "\n".join(lines).strip()

    def generate_import(self, node: IRImport) -> str:
        return f"IMPORT {node.module or ', '.join(node.names)}"

    def generate_function(self, node: IRFunction) -> str:
        params = ", ".join(node.parameters)
        body = "\n".join([f"    {self.generate(stmt)}" for stmt in node.body])
        return f"FUNCTION {node.name}({params}):\n{body}\nENDFUNCTION"

    def generate_class(self, node: IRClass) -> str:
        methods = "\n".join([f"    {self.generate(m)}" for m in node.methods])
        return f"CLASS {node.name}:\n{methods}\nENDCLASS"

    def generate_variable(self, node: IRVariable) -> str:
        return node.name

    def generate_constant(self, node: IRConstant) -> str:
        if isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    def generate_name(self, node: IRName) -> str:
        return node.name

    def generate_assignment(self, node: IRAssignment) -> str:
        val = self.generate(node.value) if node.value else "NONE"
        return f"{node.target} = {val}"

    def generate_return(self, node: IRReturn) -> str:
        val = self.generate(node.value) if node.value else ""
        return f"RETURN {val}".strip()

    def generate_expression_statement(self, node: IRExpressionStatement) -> str:
        return self.generate(node.expression)

    def generate_if(self, node: IRIf) -> str:
        cond = self.generate(node.condition)
        then_lines = "\n".join([f"    {self.generate(s)}" for s in node.then_body])
        result = f"IF {cond} THEN:\n{then_lines}"
        if node.else_body:
            else_lines = "\n".join([f"    {self.generate(s)}" for s in node.else_body])
            result += f"\nELSE:\n{else_lines}"
        result += "\nENDIF"
        return result

    def generate_for(self, node: IRFor) -> str:
        iter_str = self.generate(node.iterable)
        body_lines = "\n".join([f"    {self.generate(s)}" for s in node.body])
        return f"FOR {node.variable} IN {iter_str}:\n{body_lines}\nENDFOR"

    def generate_while(self, node: IRWhile) -> str:
        cond = self.generate(node.condition)
        body_lines = "\n".join([f"    {self.generate(s)}" for s in node.body])
        return f"WHILE {cond} DO:\n{body_lines}\nENDWHILE"

    def generate_binary_operation(self, node: IRBinaryOperation) -> str:
        left = self.generate(node.left)
        right = self.generate(node.right)
        return f"({left} {node.operator} {right})"

    def generate_unary_operation(self, node: IRUnaryOperation) -> str:
        operand = self.generate(node.operand)
        return f"{node.operator}{operand}"

    def generate_function_call(self, node: IRFunctionCall) -> str:
        args = ", ".join([self.generate(a) for a in node.arguments])
        return f"{node.name}({args})"


class TestTranslationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = TranslationEngine()
        self.engine.register_generator("dummy", DummyPseudocodeGenerator)

    def test_1_minimal_program_translation(self):
        """
        Test 1:
        Verify a minimal IRProgram can be passed through the translation engine.
        """
        empty_program = IRProgram()
        result = self.engine.translate(empty_program, "dummy")
        self.assertEqual(result, "")

    def test_2_register_and_invoke_generator(self):
        """
        Test 2:
        Verify a mock/dummy target generator can be registered and invoked.
        """
        self.assertIn("dummy", self.engine.supported_languages())

        instance_gen = DummyPseudocodeGenerator()
        self.engine.register_generator("mock_lang", instance_gen)
        self.assertIn("mock_lang", self.engine.supported_languages())

        with self.assertRaises(GeneratorNotFoundError):
            self.engine.translate(IRProgram(), "non_existent_lang")

    def test_3_node_dispatching(self):
        """
        Test 3:
        Verify the engine and generator correctly dispatch each distinct IR node type.
        """
        assign_node = IRAssignment(target="count", value=IRConstant(value=5, data_type="int"))
        gen = self.engine.get_generator("dummy")
        self.assertEqual(gen.generate(assign_node), "count = 5")

        bin_op = IRBinaryOperation(left=IRName("x"), operator="*", right=IRConstant(2, "int"))
        self.assertEqual(gen.generate(bin_op), "(x * 2)")

        if_node = IRIf(
            condition=IRBinaryOperation(left=IRName("x"), operator=">", right=IRConstant(0, "int")),
            then_body=[IRExpressionStatement(IRFunctionCall("print", [IRName("x")]))],
            else_body=[IRExpressionStatement(IRFunctionCall("print", [IRConstant(0, "int")]))],
        )
        expected_if = "IF (x > 0) THEN:\n    print(x)\nELSE:\n    print(0)\nENDIF"
        self.assertEqual(gen.generate(if_node), expected_if)

    def test_4_function_add_end_to_end_dispatch(self):
        """
        Test 4:
        Verify a simple IR function (add(a, b): return a + b) can be passed
        through the engine and reaches the target generator correctly.
        """
        func_node = IRFunction(
            name="add",
            parameters=["a", "b"],
            body=[
                IRReturn(
                    value=IRBinaryOperation(
                        left=IRName(name="a"),
                        operator="+",
                        right=IRName(name="b"),
                    )
                )
            ],
        )
        program = IRProgram(functions=[func_node])

        output = self.engine.translate(program, "dummy")
        expected_output = "FUNCTION add(a, b):\n    RETURN (a + b)\nENDFUNCTION"
        self.assertEqual(output, expected_output)

    def test_5_unsupported_node_produces_controlled_error(self):

        class UnknownCustomNode(IRNode):
            pass

        unsupported_node = UnknownCustomNode()
        gen = self.engine.get_generator("dummy")

        with self.assertRaises(UnsupportedIRNodeError) as ctx:
            gen.generate(unsupported_node)

        self.assertIn("UnknownCustomNode", str(ctx.exception))

    def test_6_extensibility_without_modifying_engine(self):
        """
        Test 6:
        Verify the target-generator interface can be extended without modifying
        the core translation engine by implementing and registering a new generator.
        """
        class MiniCustomGenerator(BaseCodeGenerator):
            def generate_program(self, node: IRProgram) -> str:
                return "CUSTOM_PROGRAM_START"

            def generate_import(self, node: IRImport) -> str: return ""
            def generate_function(self, node: IRFunction) -> str: return ""
            def generate_class(self, node: IRClass) -> str: return ""
            def generate_variable(self, node: IRVariable) -> str: return ""
            def generate_constant(self, node: IRConstant) -> str: return ""
            def generate_name(self, node: IRName) -> str: return ""
            def generate_assignment(self, node: IRAssignment) -> str: return ""
            def generate_return(self, node: IRReturn) -> str: return ""
            def generate_expression_statement(self, node: IRExpressionStatement) -> str: return ""
            def generate_if(self, node: IRIf) -> str: return ""
            def generate_for(self, node: IRFor) -> str: return ""
            def generate_while(self, node: IRWhile) -> str: return ""
            def generate_binary_operation(self, node: IRBinaryOperation) -> str: return ""
            def generate_unary_operation(self, node: IRUnaryOperation) -> str: return ""
            def generate_function_call(self, node: IRFunctionCall) -> str: return ""

        self.engine.register_generator("mini_custom", MiniCustomGenerator)
        result = self.engine.translate(IRProgram(), "mini_custom")
        self.assertEqual(result, "CUSTOM_PROGRAM_START")


if __name__ == "__main__":
    unittest.main()
