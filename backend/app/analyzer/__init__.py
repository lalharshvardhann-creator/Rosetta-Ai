from typing import Any, Dict
from .complexity_analyzer import ComplexityAnalyzer, ComplexityRank, ComplexityResult, analyze_complexity
from .pseudocode_generator import PseudocodeGenerator, generate_pseudocode
from .python_parser import PythonASTAnalyzer, analyze_python_code


def analyze_code(source_code: str) -> Dict[str, Any]:

    raw_source = source_code if source_code is not None else ""
    trimmed = raw_source.strip()

    if not trimmed:
        return {
            "success": True,
            "pseudocode": "START\nEND",
            "time_complexity": "O(1)",
            "time_explanation": "Empty source code performs no operations.",
            "space_complexity": "O(1)",
            "space_explanation": "Empty source code uses no auxiliary memory.",
        }

    pseudocode = generate_pseudocode(trimmed)
    complexity = analyze_complexity(trimmed)

    return {
        "success": True,
        "pseudocode": pseudocode,
        "time_complexity": complexity.time_complexity,
        "time_explanation": complexity.time_explanation,
        "space_complexity": complexity.space_complexity,
        "space_explanation": complexity.space_explanation,
    }


__all__ = [
    "PythonASTAnalyzer",
    "analyze_python_code",
    "PseudocodeGenerator",
    "generate_pseudocode",
    "ComplexityAnalyzer",
    "ComplexityRank",
    "ComplexityResult",
    "analyze_complexity",
    "analyze_code",
]
