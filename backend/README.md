# Rosetta AI - Backend Service ⚙️

## Purpose
The backend handles all compute-heavy and sensitive operations:
- Receiving code snippets from the frontend.
- Performing Abstract Syntax Tree (AST) parsing and syntax checks.
- Orchestrating LLM translation prompts and API interactions.
- Validating the generated code for syntax errors before sending it back.

## Planned Directory Structure (Upcoming Phases)
```
backend/
├── app/
│   ├── api/            # API route controllers
│   ├── core/           # Configs, environment settings, logger
│   ├── parsers/        # AST analyzers and language grammars
│   └── services/       # AI translation & prompt engineering logic
├── requirements.txt    # Python dependencies
└── main.py             # Server entrypoint
```
