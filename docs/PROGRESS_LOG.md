# Project AURA — Development Progress & Session Log

This document tracks completed milestones, branch status, and immediate next steps.

---

## Completed Milestones

### Stage 1: Safe Text-First MVP (Merged into `main`)
- Interactive CLI REPL (`python -m aura`) with graceful interrupts.
- Strict allowlist router with conversational fallbacks.
- AST-based safe calculator (no `eval`/`exec`, power magnitude limits, division by zero guards).
- Sandboxed file operations (`files`, `search`, `read`) with path traversal rejection.
- Tabular CSV inspection via Pandas and PDF document text extraction via PyMuPDF.

### Stage 2: Better Local Tools (Merged into `main`)
- Multi-sheet Excel workbook inspection (`excel <file> [sheet]`) using `openpyxl`.
- Safe note and text file creation (`write` and `append`) with accidental overwrite protection and safe extension enforcement (`.txt`, `.md`, `.log`, `.csv`, `.json`).
- Type-filtered workspace searches (`search <pattern> [--files|--dirs]`).

### Stage 3: Voice Output & Push-to-Talk Input (Merged into `main`)
- **Offline Text-to-Speech (TTS)** ([`src/aura/audio/tts.py`](../src/aura/audio/tts.py)):
  - Zero-latency native speech synthesis via `pyttsx3` (`sapi5` on Windows).
  - Speech sanitizer (`clean_text_for_speech`) that filters ASCII table borders, markdown lines, and bounds recitation length.
  - Runtime toggle controls: `voice on`, `voice off`, `voice status`.
  - Configurable rate and volume via environment variables (`AURA_TTS_RATE`, `AURA_TTS_VOLUME`).
- **Push-to-Talk Speech Recognition (STT)** ([`src/aura/audio/stt.py`](../src/aura/audio/stt.py)):
  - Push-to-talk microphone listening via `SpeechRecognition` and `pyaudio`.
  - Triggered on command: `listen` / `ptt`.
  - Strict privacy compliance: **Zero audio recording or retention on disk**.
  - Automatic fallback to typed keyboard input if microphone is unavailable or fails.
- **Automated Tests**: 45 unit and security tests passing.

---

### Stage 4: Online AI Provider Integration (Merged into `main`)
- **Pluggable Provider Architecture** ([`src/aura/providers/base.py`](../src/aura/providers/base.py)):
  - Abstract `BaseLLMProvider` interface defining availability checks, model identification, and response generation.
- **NVIDIA NIM Provider — Primary** ([`src/aura/providers/nvidia.py`](../src/aura/providers/nvidia.py)):
  - OpenAI-compatible Chat Completions REST API over standard `urllib.request` (zero SDK dependencies).
  - Authenticated via `NVIDIA_API_KEY` (`Bearer nvapi-...`).
  - Default model: `nvidia/nemotron-3.5-bolt-e4b` (sub-second 0.32s ultra-low latency).
  - Comprehensive error handling: HTTP 401 (auth), HTTP 404 (account function routing), HTTP 410 (end-of-life deprecation), and HTTP 429 (rate limiting).
- **Google Gemini Provider — Fallback** ([`src/aura/providers/gemini.py`](../src/aura/providers/gemini.py)):
  - Direct HTTPS REST interface supporting both API keys and OAuth tokens.
  - Configurable via `AURA_AI_PROVIDER=gemini` and `GEMINI_API_KEY`.
- **Router & CLI Integration** ([`src/aura/router.py`](../src/aura/router.py), [`src/aura/app.py`](../src/aura/app.py)):
  - `ask <prompt>` / `ai <prompt>` / `nvidia <prompt>` explicit query commands.
  - Conversational routing that forwards natural questions to the active LLM provider.
  - Local tools (`calc`, `files`, `excel`, `pdf`, `voice`) remain 100% operational when offline or unauthenticated.
  - Live AI status indicator in terminal startup banner.
- **Automated Tests**: 65 unit and security tests passing.

---

### Stage 5: Provider-Based Web Search (Merged into `main`)
- **Pluggable Search Architecture** ([`src/aura/search/base.py`](../src/aura/search/base.py)):
  - Immutable `SearchResult` data model with title, safe direct URL, and bounded snippet.
  - Abstract `BaseSearchProvider` interface with availability and search contracts.
- **Zero-Key Search Provider** ([`src/aura/search/duckduckgo.py`](../src/aura/search/duckduckgo.py)):
  - Standard library `urllib.request` and `html.parser` implementation for DuckDuckGo.
  - Automatic extraction of actual target destination URLs from DuckDuckGo redirection links (`uddg=...`).
  - Zero external SDK or cloud API key prerequisites.
- **AI Search API Provider** ([`src/aura/search/tavily.py`](../src/aura/search/tavily.py)):
  - High-precision search API for LLM agents, activated via `AURA_SEARCH_PROVIDER=tavily` and `TAVILY_API_KEY`.
- **Untrusted Content & Prompt Injection Defenses** ([`src/aura/search/safety.py`](../src/aura/search/safety.py)):
  - Strict URL scheme allowlisting (`http` and `https` only; blocked `javascript:`, `file:`, `data:`, `blob:`).
  - Output bounding on titles and snippets to prevent buffer bloat or terminal flooding.
  - Regex-based defanging for prompt-hijacking directives (e.g. `Ignore previous instructions`, `### System:`, `[INST]`).
  - Sandboxed prompt isolation (`<unverified_external_web_search_results>`) to instruct LLMs that web excerpts are strictly untrusted reference data.
- **Command Router Integration** ([`src/aura/router.py`](../src/aura/router.py)):
  - `web <query>`: Direct web search showing numbered titles, URLs, and summaries.
  - `webask <query>`: Grounded AI search. Synthesizes answers using NVIDIA NIM / Gemini with inline citations `[1]`, `[2]` and attaches source links.
  - Live Web Search status indicator in terminal startup banner ([`src/aura/app.py`](../src/aura/app.py)).
- **Automated Tests**: 84 unit and security tests passing.

---

### Stage 6: Tasks and Reminders (Merged into `main`)
- **SQLite Persistence Engine** ([`src/aura/tasks/db.py`](../src/aura/tasks/db.py), [`src/aura/tasks/models.py`](../src/aura/tasks/models.py)):
  - Zero-dependency embedded database storing tasks and reminders in `data/aura_tasks.db`.
  - Atomic transactions, indexed queries, and guaranteed connection closure preventing Windows file-lock contention.
  - Full CRUD operations with input validation and character bounds.
- **Natural Time Parsing** ([`src/aura/tasks/time_parser.py`](../src/aura/tasks/time_parser.py)):
  - Relative intervals (`in 15m`, `in 2h`, `in 30s`, `in 1 day`).
  - Clock times (`at 15:30`, `at 3pm`, `at 9:30am`) with automatic day roll-over.
  - Flexible natural reminder commands (`remind in 15m to take a break`, `remind at 17:00 to clock out`).
- **Background Reminder Scheduler** ([`src/aura/tasks/scheduler.py`](../src/aura/tasks/scheduler.py)):
  - Non-blocking daemon background worker polling due reminders every 2s.
  - Atomic status transition (`scheduled` -> `fired`) to prevent duplicate alerts.
  - Dispatches terminal alerts (`[REMINDER ALERT] <msg>`) and spoken audio via offline TTS when voice is enabled.
- **CLI & Router Integration** ([`src/aura/router.py`](../src/aura/router.py), [`src/aura/tasks/formatters.py`](../src/aura/tasks/formatters.py)):
  - `task add <title> [--priority low|med|high] [--due YYYY-MM-DD]`
  - `task list [--all|--done|--pending]`
  - `task done <id>`, `task delete <id>`, `task clear`
  - `remind <when> to <message>`
  - `reminders` & `reminder cancel <id>`
  - Live tasks and reminders count in terminal startup banner ([`src/aura/app.py`](../src/aura/app.py)).
- **Automated Tests**: 101 unit and security tests passing (17 new task and reminder tests).

---

## Next Milestone: Stage 7 — Wake Word Detection
- Offline wake-word detection engine (e.g. `openWakeWord`).
- Explicit opt-in activation and visible listening indicators.
- Immediate pause/stop controls ensuring zero silent listening.
