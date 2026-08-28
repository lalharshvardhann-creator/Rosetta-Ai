from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.analyzer import analyze_code
from app.ir import build_ir
from app.translation import (
    GeneratorNotFoundError,
    TranslationEngine,
    TranslationError,
    UnsupportedIRNodeError,
)


app = FastAPI(
    title="Rosetta AI API",
    description="Universal Multi-Language Code Translation Engine powered by AST and IR.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


engine = TranslationEngine(register_defaults=True)


class TranslateRequest(BaseModel):
    source: Optional[str] = Field(
        None,
        description="Python source code to translate",
    )
    source_code: Optional[str] = Field(
        None,
        description="Python source code to translate (alias)",
    )
    target_language: Optional[str] = Field(
        None,
        description="Target language identifier (e.g. 'java', 'cpp', 'javascript')",
    )


class TranslateResponse(BaseModel):
    success: bool
    source_language: Optional[str] = "python"
    target_language: Optional[str] = None
    code: Optional[str] = None
    error: Optional[str] = None


class AnalyzeRequest(BaseModel):
    source: Optional[str] = Field(
        None,
        description="Python source code to analyze",
    )
    source_code: Optional[str] = Field(
        None,
        description="Python source code to analyze (alias)",
    )


class AnalyzeResponse(BaseModel):
    success: bool
    pseudocode: Optional[str] = None
    time_complexity: Optional[str] = None
    time_explanation: Optional[str] = None
    space_complexity: Optional[str] = None
    space_explanation: Optional[str] = None
    error: Optional[str] = None


MAX_SOURCE_LENGTH = 100_000


def _extract_source(
    source: Optional[str],
    source_code: Optional[str],
) -> str:
    """Resolve the source/source_code alias and validate the input."""
    raw = source if source is not None else source_code

    if raw is None or not isinstance(raw, str) or not raw.strip():
        raise ValueError("source must not be empty.")

    if len(raw) > MAX_SOURCE_LENGTH:
        raise ValueError(
            f"Source code exceeds maximum allowed length of "
            f"{MAX_SOURCE_LENGTH:,} characters."
        )

    return raw.strip()


@app.get("/api/health")
async def health_check():
    """Return system status and registered target languages."""
    return {
        "status": "ok",
        "engine": "Rosetta AI",
        "supported_languages": engine.supported_languages(),
    }


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_code(request: TranslateRequest):
    """
    Translate Python source code into the requested target language
    through the AST -> IR -> TranslationEngine pipeline.
    """
    try:
        source_code = _extract_source(
            request.source,
            request.source_code,
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "source_language": "python",
                "target_language": None,
                "code": None,
                "error": str(e),
            },
        )

    if (
        not request.target_language
        or not isinstance(request.target_language, str)
        or not request.target_language.strip()
    ):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "source_language": "python",
                "target_language": None,
                "code": None,
                "error": "target_language must not be empty.",
            },
        )

    norm_lang = engine._normalize_lang(request.target_language.strip())

    supported_languages = engine.supported_languages()

    if norm_lang not in supported_languages:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "source_language": "python",
                "target_language": None,
                "code": None,
                "error": (
                    f"Unsupported target language: "
                    f"'{request.target_language}'. "
                    f"Supported languages: {supported_languages}"
                ),
            },
        )

    try:
        ir_program = build_ir(source_code)
    except SyntaxError as e:
        line_info = f" on line {e.lineno}" if e.lineno else ""

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "source_language": "python",
                "target_language": norm_lang,
                "code": None,
                "error": (
                    f"Python syntax error{line_info}: "
                    f"{e.msg or str(e)}"
                ),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "source_language": "python",
                "target_language": norm_lang,
                "code": None,
                "error": f"Failed to analyze source code: {str(e)}",
            },
        )

    try:
        translated_code = engine.translate(
            ir_program,
            norm_lang,
        )

        return {
            "success": True,
            "source_language": "python",
            "target_language": norm_lang,
            "code": translated_code,
            "error": None,
        }

    except GeneratorNotFoundError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "source_language": "python",
                "target_language": norm_lang,
                "code": None,
                "error": str(e),
            },
        )

    except (TranslationError, UnsupportedIRNodeError) as e:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "source_language": "python",
                "target_language": norm_lang,
                "code": None,
                "error": f"Translation error: {str(e)}",
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "source_language": "python",
                "target_language": norm_lang,
                "code": None,
                "error": f"Internal translation failure: {str(e)}",
            },
        )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_code_endpoint(request: AnalyzeRequest):
    """
    Analyze Python source code and generate pseudocode
    and estimated Big-O time and space complexity.
    """
    try:
        source_code = _extract_source(
            request.source,
            request.source_code,
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "pseudocode": None,
                "time_complexity": None,
                "time_explanation": None,
                "space_complexity": None,
                "space_explanation": None,
                "error": str(e),
            },
        )

    try:
        result = analyze_code(source_code)

        return {
            "success": True,
            "pseudocode": result.get("pseudocode", ""),
            "time_complexity": result.get(
                "time_complexity",
                "O(1)",
            ),
            "time_explanation": result.get(
                "time_explanation",
                "",
            ),
            "space_complexity": result.get(
                "space_complexity",
                "O(1)",
            ),
            "space_explanation": result.get(
                "space_explanation",
                "",
            ),
            "error": None,
        }

    except SyntaxError as e:
        line_info = f" on line {e.lineno}" if e.lineno else ""

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "pseudocode": None,
                "time_complexity": None,
                "time_explanation": None,
                "space_complexity": None,
                "space_explanation": None,
                "error": (
                    f"Python syntax error{line_info}: "
                    f"{e.msg or str(e)}"
                ),
            },
        )

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "pseudocode": None,
                "time_complexity": None,
                "time_explanation": None,
                "space_complexity": None,
                "space_explanation": None,
                "error": str(e),
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "pseudocode": None,
                "time_complexity": None,
                "time_explanation": None,
                "space_complexity": None,
                "space_explanation": None,
                "error": f"Internal analysis failure: {str(e)}",
            },
        )
    
