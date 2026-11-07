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

4. (Optional) Install PDF document support, voice audio, and test runner:
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
  Version: 0.1.0 | Mode: Voice & Command
======================================================
  Workspace  : C:\path\to\project\data
  Voice TTS  : [OFF] (use 'voice on' / 'voice off')
  Voice PTT  : [READY (type 'listen')]
  Wake Word  : [DISABLED (type 'wakeword on')]
  Online AI  : [NVIDIA NIM (nvidia/nemotron-3.5-bolt-e4b)]
  Web Search : [DuckDuckGo (Zero-Key)]
  Tasks / Rem: [0 pending / 0 scheduled]
  Hint       : Type 'help' for commands, 'exit' to quit.
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
| `task [add/list/done/del]` | `task add Prepare slides --priority high` | Create and manage persistent to-do tasks stored in SQLite |
| `remind <when> to <msg>` | `remind in 15m to take a break` | Schedule a timed reminder with console and spoken TTS alert |
| `reminders` | `reminders` or `reminder cancel 1` | List scheduled reminders or cancel a reminder |
| `voice [on/off]` | `voice on` or `voice off` | Toggle spoken audio responses via offline Text-to-Speech (TTS) |
| `listen` | `listen` | Activate push-to-talk microphone to speak your command |
| `listen wake` | `listen wake` | Activate hands-free continuous voice loop ("Hey AURA") |
| `wakeword [on/off/status]` | `wakeword on` or `wakeword status` | Toggle or inspect wake-word detection engine and threshold |
| `ask <question>` | `ask what is quantum computing?` | Query NVIDIA NIM conversational AI (requires `NVIDIA_API_KEY`) |
| `web <query>` | `web latest space missions` | Search live web and display cited sources, titles, and links |
| `webask <query>` | `webask who won the 2024 Nobel Prize in Physics?` | Search live web and synthesize grounded answer with source citations |
| `exit` / `quit` / `bye` | `exit` | Terminate session cleanly |

---

## 4. Security & Safety Boundaries

- **Zero Arbitrary Execution**: AURA never invokes `eval`, `exec`, or unrestricted shell subprocesses.
- **AST Mathematical Validation**: Expressions are parsed using `ast.parse` with an allowlist of operators and functions.
- **Sandboxed Workspace**: File inspection and creation are strictly confined to the directory configured via `AURA_WORKSPACE_DIR` (defaults to `./data`). Path traversal (`../`, absolute drive access) is automatically blocked.
- **Zero Audio Retention (Privacy First)**: Microphone audio (both push-to-talk and wake-word scanning) operates purely within transient in-memory ring buffers. AURA **never** records, streams, or saves microphone audio files to disk.
- **Explicit Opt-In Wake-Word Detection**: Wake-word scanning is disabled by default and never runs always-on silently. Visible listening indicators are shown during operation, and scanning pauses during speech synthesis to prevent acoustic feedback loops.
- **Persistent SQLite Task Storage**: Tasks and reminders use parameterized queries (`?`) preventing SQL injection. Database files are excluded from version control via `.gitignore`.
- **Prompt Injection Defense & URL Scheme Allowlist**: Web searches validate URLs to only allow `http`/`https`. Untrusted search snippets are defanged for prompt injection attacks and wrapped in sandboxed reference tags.
- **Overwrite Protection**: The assistant will not silently replace user files without explicit `--overwrite` or `append`.
- **Graceful Degradation**: Optional dependencies (such as `pyttsx3`, `pyaudio`, `openpyxl`, or `pymupdf`) provide clear setup instructions instead of crashing.

---

## 5. Running Automated Tests

Run the full pytest suite with:

```bash
pytest
```
