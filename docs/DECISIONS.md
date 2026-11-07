# Project AURA — Architectural Decisions & Technical Rationale

This document logs significant architectural and design choices, alternatives considered, and trade-offs made during development.

---

### Decision 1: Safe AST-Based Math Evaluation Instead of `eval()`
- **Context**: The assistant needs to evaluate arithmetic expressions from text or voice input.
- **Decision**: Implemented an explicit Abstract Syntax Tree (AST) visitor allowlisting binary operations, unary signs, standard math functions (`sqrt`, `sin`, `log`, etc.), and constants (`pi`, `e`).
- **Rationale**: Built-in `eval()` exposes arbitrary code execution vulnerabilities (`__import__('os').system(...)`). The AST approach guarantees safe execution with bounded power exponentiation (`a ** b` where $b \le 1000$).

---

### Decision 2: Workspace Boundary Sandboxing
- **Context**: File-reading and file-listing tools must allow users to inspect documents without granting broad host file access.
- **Decision**: Bound all workspace operations to `AURA_WORKSPACE_DIR` (defaulting to `./data`), resolving absolute paths and rejecting any path traversal sequences (`../`, root path escape).
- **Rationale**: Protects system files, source code, and user credentials outside the designated working folder.

---

### Decision 3: Standard Library-First Architecture
- **Context**: Keeping installation lightweight and avoiding build toolchain failures on varied platforms (especially Windows with Python 3.13).
- **Decision**: Core MVP commands rely strictly on the Python standard library (`ast`, `math`, `pathlib`, `json`, `datetime`, `logging`). Third-party tools (`pandas`, `pymupdf`, `openpyxl`, `pyttsx3`, `pyaudio`) are optional or gracefully isolated.
- **Rationale**: Maximizes reliability and reproducibility across environments without installation roadblocks.

---

### Decision 4: Safe Note & File Creation (Stage 2)
- **Context**: Users need to create notes and save text documents safely without risking corruption of system files or accidental loss of work.
- **Decision**: Enforced extension allowlists (`.txt`, `.md`, `.log`, `.csv`, `.json`), strict directory sandboxing, and overwrite protection (requires explicit `--overwrite` flag, or `append` command).
- **Rationale**: Eliminates silent file overwrites while ensuring executables (`.exe`, `.bat`, `.py`) cannot be written into arbitrary directories.

---

### Decision 5: Read-Only OpenPyXL for Tabular Excel Workbooks (Stage 2)
- **Context**: Excel workbooks (`.xlsx`) need inspection similar to CSVs.
- **Decision**: Use `openpyxl.load_workbook(filename, read_only=True, data_only=True)`.
- **Rationale**: Fast streaming evaluation, low memory consumption on large spreadsheets, and evaluates formula results rather than raw formula text.

---

### Decision 6: Case-Insensitive Pattern Matching with Type Filtering (Stage 2)
- **Context**: Finding files inside workspace folders.
- **Decision**: Support glob patterns (e.g. `*.csv`) as well as substring matching, with optional `--files` and `--dirs` flags.
- **Rationale**: Matches intuitive terminal search habits while keeping boundaries safe.

---

### Decision 7: Standardized Testing & Modular Isolation
- **Context**: High test coverage needed to guarantee stability before subsequent stages.
- **Decision**: Write granular unit tests targeting each tool module in isolation, avoiding brittle end-to-end mocks.
- **Rationale**: Rapid feedback loop with high confidence across edge cases and security boundary rejections.

---

### Decision 8: Offline Speech Synthesis via `pyttsx3` with Output Sanitization
- **Context**: Voice output is needed without cloud latency, API key requirements, or ongoing costs.
- **Decision**: Integrated `pyttsx3` using native OS speech engines (`sapi5` on Windows, `nsss` on macOS, `espeak` on Linux) coupled with a regex-based `clean_text_for_speech` sanitizer.
- **Rationale**: Zero external network dependency, zero cost, and prevents ASCII table borders or markdown formatting from being awkwardly vocalized.

---

### Decision 9: Push-to-Talk Speech Recognition with Zero Audio Retention
- **Context**: Voice input is needed while preserving keyboard fallback and strict user privacy.
- **Decision**: Use push-to-talk speech recognition activated by user command (`listen`). Never record, stream, or retain audio to local disk files.
- **Rationale**: Complies directly with Section 7 security and privacy rules while avoiding constant, silent background listening.

---

### Decision 10: Pluggable Online AI Architecture with Standard Library HTTPS (NVIDIA NIM Primary, Google Gemini Fallback)
- **Context**: Stage 4 introduces cloud LLMs for answering freeform conversational questions. We need fast, reliable models with zero third-party package compilation friction.
- **Decision**: Implemented `BaseLLMProvider` interface with `NvidiaProvider` as primary (OpenAI-compatible REST API hitting `https://integrate.api.nvidia.com/v1/chat/completions` using `nvidia/nemotron-3.5-bolt-e4b`) and `GeminiProvider` as fallback, both using Python's standard library `urllib.request`.
- **Rationale**: Zero SDK dependency footprint, sub-second latency (0.32s), robust error categorization (HTTP 401, 404, 410, 429), and seamless fallback to local tools when offline or unconfigured.


---

### Decision 11: Pluggable Web Search with Zero-Key Default & Prompt Injection Defense (Stage 5)
- **Context**: Stage 5 requires web search to look up external and current information, returning concise sources and links, while protecting against untrusted web inputs and prompt injection.
- **Decision**: Implemented `BaseSearchProvider` with `DuckDuckGoSearchProvider` as the zero-key out-of-the-box default (using standard library `urllib` and `html.parser`), alongside `TavilySearchProvider` for structured AI searches. Enforced URL validation (`http`/`https` only), output bounding, regex defanging of prompt injection directives, and sandboxed prompt wrapping (`<unverified_external_web_search_results>`) for `webask`.
- **Rationale**: Keeps AURA completely usable out-of-the-box without requiring paid API keys, isolates untrusted third-party web content from assistant reasoning, and gives users both raw (`web`) and AI-synthesized (`webask`) modes.


---

### Decision 12: Embedded SQLite Storage & Threaded Daemon Scheduler for Tasks and Reminders (Stage 6)
- **Context**: Stage 6 requires persistent task tracking and timed reminders without external cloud databases, heavy ORMs, or background daemon installation requirements.
- **Decision**: Implemented `TaskDatabase` utilizing Python's built-in `sqlite3` module with an embedded database stored inside `data/aura_tasks.db`. Provided strict connection lifecycle management via a context manager to eliminate Windows file-locking issues. Implemented a non-blocking `ReminderScheduler` running on a daemon thread polling due timestamps and executing an atomic status transition before notification dispatch.
- **Rationale**: Keeps AURA completely self-contained, offline-capable, cross-platform, and fast. Eliminates third-party database daemon dependencies while providing thread-safe CRUD and notifications with TTS integration.
