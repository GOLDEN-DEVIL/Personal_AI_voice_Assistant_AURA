# Project AURA — AI Utility & Response Assistant

A modular, secure, and extensible desktop command & voice assistant foundation written in modern Python.

---

## 1. Quickstart & Installation

### Prerequisites
- Python 3.11 or newer (tested with Python 3.13)
- Windows, macOS, or Linux

### Installation

1. Clone the repository and navigate into the project directory:
   ```bash
   git clone https://github.com/GOLDEN-DEVIL/Personal_AI_voice_Assistant_AURA.git
   cd Personal_AI_voice_Assistant_AURA
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
  Workspace: ./data
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
| `search <pattern>` | `search *.csv` or `search notes --files` | Find files/folders within workspace with optional `--files` / `--dirs` filter |
| `read <filename>` | `read notes.txt` | Safely preview text documents with bounded character limits |
| `write <file> <text>` | `write notes.txt Meeting notes` | Safely create a new text file or note in workspace with overwrite protection |
| `append <file> <text>` | `append notes.txt New action item` | Safely append content to an existing workspace document |
| `csv <filename>` | `csv sample.csv` | Inspect CSV column types, dimensions, and top-5 preview |
| `excel <file> [sheet]` | `excel sample.xlsx Financials` | Inspect Excel workbook sheets, columns, and previews via openpyxl |
| `pdf <filename>` | `pdf manual.pdf` | Inspect PDF metadata and extracted text (requires `pymupdf`) |
| `voice [on/off]` | `voice on` or `voice off` | Toggle spoken audio responses via offline Text-to-Speech (TTS) |
| `listen` | `listen` | Activate push-to-talk microphone to speak your command |
| `exit` / `quit` / `bye` | `exit` | Terminate session cleanly |

---

## 4. Security & Safety Boundaries

- **Zero Arbitrary Execution**: AURA never invokes `eval`, `exec`, or unrestricted shell subprocesses.
- **AST Mathematical Validation**: Expressions are parsed using `ast.parse` with an allowlist of operators and functions.
- **Sandboxed Workspace**: File inspection and creation are strictly confined to the directory configured via `AURA_WORKSPACE_DIR` (defaults to `./data`). Path traversal (`../`, absolute drive access) is automatically blocked.
- **Zero Audio Retention (Privacy First)**: Speech recognition operates purely in-memory on push-to-talk (`listen`). AURA **never** records, streams, or saves microphone audio files to disk.
- **Overwrite Protection**: The assistant will not silently replace user files without explicit `--overwrite` or `append`.
- **Graceful Degradation**: Optional dependencies (such as `pyttsx3`, `pyaudio`, `openpyxl`, or `pymupdf`) provide clear setup instructions instead of crashing.

---

## 5. Running Automated Tests

Run the full pytest suite:

```bash
python -m pytest -v
```

All 45 automated unit and security tests will execute:
- Safe calculator evaluation & boundary rejection
- Text-to-Speech text sanitization & speech engine controls
- Speech-to-Text mock transcription and hardware error handling
- Path traversal & workspace boundary containment
- Tabular CSV & multi-sheet Excel schema validations
- Command routing, voice controls, & conversational fallbacks

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
