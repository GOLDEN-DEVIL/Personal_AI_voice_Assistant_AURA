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
- **Automated Tests**: 101 unit and security tests passing.

---

### Stage 7: Wake Word Detection (Merged into `main`)
- **Wake-Word Detection Engine** ([`src/aura/audio/wakeword.py`](../src/aura/audio/wakeword.py)):
  - Offline wake-word detection engine with state machine (`DISABLED`, `IDLE`, `LISTENING`, `TRIGGERED`, `PAUSED`).
  - Pluggable backend support: `openWakeWord` neural detection if installed, with a zero-dependency `SpeechRecognition` keyword fallback (`"hey aura"` / `"aura"`).
  - Explicit user opt-in: **Disabled by default** (`AURA_WAKE_WORD_ENABLED=false`). Never runs always-on listening silently.
  - Strict privacy compliance: **Zero audio recording or retention on disk**. Raw audio frames are processed strictly in RAM ring buffers and immediately discarded.
  - Acoustic echo/feedback suppression: Automatically pauses wake-word detection while TTS is speaking and resumes after playback.
- **Hands-Free Interactive Voice Loop** ([`src/aura/app.py`](../src/aura/app.py)):
  - Activated via `listen wake` / `wake listen` / `voice loop`.
  - Continuous hands-free cycle: Wake Word ("Hey AURA") -> Speech-to-Text -> Intent Router -> Text-to-Speech response -> Return to wake-word listening.
  - Clear visual terminal indicators: `[WAKE WORD: ACTIVE - Listening for "Hey AURA"]` and `[WAKE WORD DETECTED]`.
  - Immediate interruption controls: Say "stop listening" or press `Ctrl+C` to return instantly to the command prompt.
- **Router & CLI Controls** ([`src/aura/router.py`](../src/aura/router.py)):
  - `wakeword on`: Activates wake-word listening.
  - `wakeword off`: Immediately disables wake-word listening.
  - `wakeword status`: Displays current operating state, trigger phrase, sensitivity threshold, and hardware engine.
  - Live wake-word state indicator in terminal startup banner.
- **Automated Tests**: 111 unit and security tests passing (10 new wake-word tests).

---

### Stage 8: Persistent Memory & Dialogue Context (Merged into `main`)
- **Long-Term Memory Store** ([`src/aura/memory/store.py`](../src/aura/memory/store.py), [`src/aura/memory/models.py`](../src/aura/memory/models.py)):
  - Dedicated SQLite storage in `data/aura_memory.db` for persistent user facts, preferences, and notes.
  - Complete CRUD operations: `add_memory`, `list_memories`, `search_memories`, `get_memory`, `update_memory`, `delete_memory`, `clear_memories`.
  - Strict input validation and length bounds (max 500 chars/fact, max 500 total memories).
  - Context-managed connection pool guaranteeing clean connection closure to prevent Windows file locks.
- **Short-Term Conversational Context** ([`src/aura/memory/context.py`](../src/aura/memory/context.py)):
  - In-memory ring buffer holding the most recent $N$ dialogue turns (default 6 turns).
  - Strict privacy rule: **Volatile RAM only, zero disk retention**. Never written to SQLite or file storage.
  - Automatically wiped upon session termination or on explicit `memory session clear`.
- **AI Prompt Augmentation & Injection Security** ([`src/aura/memory/formatters.py`](../src/aura/memory/formatters.py)):
  - Safely injects stored facts and recent dialogue history into `ask` and conversational fallback prompts when enabled.
  - Sanitizes user memory content before prompt insertion, neutralizing prompt injection vectors (`ignore previous instructions`, etc.).
  - Bounded prompt augmentation token footprint (max 1500 chars).
- **Router & CLI Commands** ([`src/aura/router.py`](../src/aura/router.py)):
  - `remember <fact>` / `memory remember <fact> [--category <cat>]`: Save a fact.
  - `memory list [--category <cat>]`: List stored facts.
  - `memory search <query>`: Search stored facts.
  - `memory update <id> <new_text>`: Edit a stored fact.
  - `memory forget <id>` / `forget <id>`: Delete an individual fact.
  - `memory clear [--force]`: Wipe all facts with destructive confirmation requirement.
  - `memory session [clear]`: Inspect or wipe ephemeral dialogue turns.
  - `memory inject [on|off]`: Toggle auto-injection into AI prompts.
  - `memory on` / `memory off`: Toggle memory subsystem.
  - `memory status`: Comprehensive status report.
  - Terminal startup banner indicates live memory status.
- **Automated Tests**: 121 unit and security tests passing (10 new memory tests).

---

## Next Milestone: Stage 9 — Safe Application & Website Control
- Platform-aware application launcher with strict allowlist.
- Safe browser URL opening with scheme and domain validation.
- Zero arbitrary shell command execution.
