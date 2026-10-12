# Project AURA — AI Utility & Response Assistant

A modular, secure, and extensible desktop command & voice assistant foundation written in modern Python.

---

## 1. Quickstart & Installation

### Prerequisites
- Python 3.11 or newer (tested with Python 3.13)
- Windows, macOS, or Linux

### Installation

1. Clone or navigate to the project directory:
   ```bash
   cd c:\vscodeing\PROJECT_SEM_3\AI_voice_assistant_AURA
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install the package in editable mode with dependencies:
   ```bash
   pip install -e .
   ```

4. (Optional) Install PDF document support and test runner:
   ```bash
   pip install -e .[all]
   ```

---

## 2. Running AURA

Start the interactive assistant by running:

```bash
python -m aura
```

You will be greeted by the AURA banner:
```text
======================================================
  Project AURA - AI Utility & Response Assistant
  Version: 0.1.0 | Mode: Local MVP
======================================================
  Workspace: C:\vscodeing\PROJECT_SEM_3\AI_voice_assistant_AURA\data
  Status   : Ready for input
  Hint     : Type 'help' for commands, 'exit' to quit.
------------------------------------------------------

AURA > 
```

---

## 3. Supported Commands

| Command | Example | Description |
|---|---|---|
| `help` | `help` | List all available commands and syntax |
| `time` | `time` | Show current local time and timezone |
| `date` | `date` | Show current date and day of week |
| `calc <expr>` | `calc (120 * 4) + sqrt(144)` | Safely evaluate arithmetic via AST parser (no `eval`) |
| `files [subpath]` | `files` or `files subfolder` | List contents of the sandboxed workspace folder |
| `search <pattern>` | `search *.csv` or `search notes` | Find files within workspace matching a glob pattern |
| `read <filename>` | `read notes.txt` | Safely preview text documents with bounded character limits |
| `csv <filename>` | `csv sample.csv` | Inspect CSV column types, dimensions, and top-5 preview |
| `pdf <filename>` | `pdf manual.pdf` | Inspect PDF metadata and extracted text (requires `pymupdf`) |
| `exit` / `quit` / `bye` | `exit` | Terminate session cleanly |

---

## 4. Security & Safety Boundaries

- **Zero Arbitrary Execution**: AURA never invokes `eval`, `exec`, or unrestricted shell subprocesses.
- **AST Mathematical Validation**: Expressions are parsed using `ast.parse` with an allowlist of operators and functions.
- **Sandboxed Workspace**: File inspection is strictly confined to the directory configured via `AURA_WORKSPACE_DIR` (defaults to `./data`). Path traversal (`../`, absolute drive access) is automatically blocked.
- **Read-Only MVP**: The assistant cannot overwrite, delete, or upload local files.
- **Graceful Degradation**: Optional dependencies (such as `pymupdf` for PDFs) provide clear setup instructions instead of crashing.

---

## 5. Running Automated Tests

Run the full pytest suite:

```bash
python -m pytest -v
```

All 25 automated unit and security tests will execute:
- Safe calculator evaluation & boundary rejection
- Path traversal & workspace boundary containment
- Tabular CSV schema validation & previews
- Command routing & conversational fallbacks

---

## 6. Architecture & Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): System layout and request lifecycle
- [docs/SECURITY.md](docs/SECURITY.md): Threat model, privacy, and safety boundaries
- [docs/DECISIONS.md](docs/DECISIONS.md): Architectural decisions and trade-offs log

---

## 7. Roadmap & Next Stages

- **Stage 2**: Text file creation and expanded tabular filters (Excel support).
- **Stage 3**: Push-to-talk voice input and offline text-to-speech output (`pyttsx3`).
- **Stage 4**: Configurable online LLM provider (OpenAI, Gemini, Groq, Ollama) with fallback.
- **Stage 5**: Web search integration with citations.
- **Stage 6**: Reminders, schedules, and SQLite task persistence.
