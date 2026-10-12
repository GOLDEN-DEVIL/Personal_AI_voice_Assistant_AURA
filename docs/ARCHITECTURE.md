# Project AURA — Architecture

This document describes the high-level architecture, component boundaries, and request lifecycle of Project AURA (AI Utility & Response Assistant).

## 1. Architectural Overview

AURA is organized into loosely coupled, modular layers designed to keep the user interface separate from core tooling and safety logic.

```
       +---------------------------------------------+
       |           User Interface Layer              |
       |  - CLI REPL (`aura.app`)                    |
       |  - Future: Speech / Audio Adapter           |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |         Routing & Intent Layer              |
       |  - `CommandRouter` (`aura.router`)          |
       |  - Allowlist Verification                   |
       |  - Conversational Fallback Detector         |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |            Safety Enforcement               |
       |  - `validate_workspace_path` (`aura.safety`)|
       |  - Path Traversal Shield                    |
       |  - Output Truncation & Sanitization         |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |             Tool Handlers                   |
       |  - `basic`: time, date, formatted help      |
       |  - `calculator`: AST-based safe math eval   |
       |  - `files`: directory list & search         |
       |  - `tabular`: safe Pandas CSV inspection    |
       |  - `documents`: safe text & PyMuPDF reader  |
       +---------------------------------------------+
```

## 2. Request Lifecycle

1. **Input Ingestion**: The interactive loop in `aura.app` prompts the user (`AURA > `) and reads a string command.
2. **Parsing & Normalization**: The command string is passed to `CommandRouter.execute()`, which trims whitespace and isolates the primary command keyword from arguments.
3. **Allowlist Dispatch**:
   - The command keyword is matched against the explicit allowlist.
   - If a recognized command is found, control flows to the appropriate tool function.
   - If the input resembles conversational speech (e.g. questions or greetings), a clear notification is displayed that online AI providers are not configured yet in local MVP mode.
   - Any unrecognized command returns a friendly error directing the user to `help`.
4. **Safety & Bounds Check**:
   - File-based tools validate paths with `validate_workspace_path`, preventing any read access outside the configured `data/` directory.
   - Mathematical expressions are parsed into an Abstract Syntax Tree (AST) where only safe arithmetic and allowlisted math operations are permitted.
5. **Response Formatting**: Tool output is sanitized and formatted with clear headings and summaries before returning to the terminal.
6. **Graceful Termination**: When an exit keyword (`exit`, `quit`, `bye`) is matched, `should_exit=True` is returned and the process shuts down cleanly.

## 3. Directory Layout

```
AI_voice_assistant_AURA/
├── pyproject.toml              # Build specification & dependencies
├── README.md                   # Quickstart, setup, and usage guide
├── .gitignore                  # VCS ignore definitions
├── .env.example                # Sample environment configuration
├── data/                       # Sandboxed workspace for file operations
│   ├── .gitkeep
│   ├── sample.csv              # Test tabular file
│   └── notes.txt               # Test text file
├── docs/
│   ├── ARCHITECTURE.md         # System design & request lifecycle
│   ├── SECURITY.md             # Security boundaries & safety model
│   └── DECISIONS.md            # Technical decisions & assumptions log
├── src/
│   └── aura/
│       ├── __init__.py         # Package root & version
│       ├── __main__.py         # Entry point for 'python -m aura'
│       ├── app.py              # Interactive REPL & application driver
│       ├── config.py           # Configuration loading & defaults
│       ├── logging_config.py   # Secure structured logging
│       ├── router.py           # Command routing & allowlist
│       ├── safety.py           # Path validation & sandbox enforcement
│       └── tools/
│           ├── __init__.py
│           ├── basic.py        # Date, time, and help
│           ├── calculator.py   # Safe AST-based calculator
│           ├── documents.py    # Safe text & PDF inspection
│           ├── files.py        # Workspace file listing & glob search
│           └── tabular.py      # Pandas CSV inspection
└── tests/
    ├── test_calculator.py     # Safe math evaluation tests
    ├── test_files.py          # File listing, traversal, & reading tests
    ├── test_router.py         # Routing & fallback tests
    └── test_tabular.py        # CSV parsing & boundary tests
```
