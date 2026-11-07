# Project AURA — Architecture

This document describes the high-level architecture, component boundaries, and request lifecycle of Project AURA (AI Utility & Response Assistant).

## 1. Architectural Overview

AURA is organized into loosely coupled, modular layers designed to keep the user interface separate from core tooling, audio pipelines, AI providers, web search, background scheduling, and safety logic.

```
       +-------------------------------------------------------+
       |                 User Interface Layer                  |
       |  - CLI REPL (`aura.app`)                              |
       |  - Audio I/O (`aura.audio`): pyttsx3 TTS & STT Listen |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |               Routing & Intent Layer                  |
       |  - `CommandRouter` (`aura.router`)                    |
       |  - Allowlist Tool Verification                        |
       |  - Conversational Fallback & LLM Dispatcher           |
       +-------------------------------------------------------+
          |                   |                     |
          v                   v                     v
   +--------------+   +---------------+   +-------------------+
   | Safety Layer |   |  Web Search   |   |    AI Providers   |
   | - Sandbox    |   | - BaseSearch  |   |  - NvidiaProvider |
   | - Injection  |   | - DuckDuckGo  |   |  - GeminiProvider |
   | - AST Math   |   | - Tavily REST |   |  - OpenAI REST    |
   +--------------+   +---------------+   +-------------------+
          |                   |                     |
          +───────────────────┼─────────────────────+
                              |
                              v
       +-------------------------------------------------------+
       |              Tool & Persistence Handlers              |
       |  - `basic`: time, date, formatted help                |
       |  - `calculator`: AST-based safe math eval             |
       |  - `files`: directory list, type-filtered glob search |
       |  - `tabular`: Pandas CSV & openpyxl Excel inspection  |
       |  - `documents`: safe text read/write & PyMuPDF reader |
       |  - `search`: live web search & grounded AI synthesis  |
       |  - `tasks`: SQLite task storage & daemon scheduler    |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |           Storage & Background Services               |
       |  - SQLite: `data/aura_tasks.db` (tasks & reminders)   |
       |  - `ReminderScheduler`: Daemon thread polling due alerts |
       +-------------------------------------------------------+
```

## 2. Request Lifecycle

1. **Input Ingestion**:
   - Keyboard: Interactive loop in `aura.app` prompts (`AURA > `).
   - Voice: Push-to-talk trigger (`listen` / `ptt`) captures microphone audio in-memory, transcribes it via `SpeechToTextListener`, and routes the transcription.
2. **Parsing & Normalization**: The command string is passed to `CommandRouter.execute()`, trimming whitespace and isolating command keywords.
3. **Allowlist Dispatch**:
   - Local tools: `calc`, `files`, `search`, `read`, `write`, `append`, `csv`, `excel`, `pdf`, `voice`.
   - Task & Reminders: `task add`, `task list`, `task done`, `task delete`, `remind <when> to <msg>`, `reminders`, `reminder cancel <id>`.
   - Web Search: `web <query>` (citations and links) or `webask <query>` (grounded LLM synthesis).
   - Conversational AI: `ask <prompt>` or freeform query dispatched to `BaseLLMProvider`.
4. **Safety & Bounds Check**:
   - File-based tools validate paths with `validate_workspace_path`, preventing escape from `AURA_WORKSPACE_DIR` (`./data`).
   - Web URLs are verified against an `http`/`https` allowlist, defanging dangerous schemes (`javascript:`, `file:`, `data:`).
   - External search snippets are defanged for prompt injection keywords and wrapped in unverified XML tags for LLM prompts.
   - Tasks and reminders undergo title bounding and SQL injection defense via parameterized queries.
5. **Response Formatting & Vocalization**:
   - Text output is returned to the terminal.
   - If TTS is enabled (`voice on`), `TextToSpeechEngine` sanitizes formatting and vocalizes the reply.
   - Asynchronous reminders trigger a `[REMINDER ALERT]` console banner and spoken TTS announcement.
6. **Graceful Termination**: `exit`, `quit`, or `bye` cleanly terminates the session and shuts down background daemon threads.

## 3. Directory Layout

```
AI_voice_assistant_AURA/
├── pyproject.toml              # Build specification & dependencies
├── README.md                   # Quickstart, setup, and usage guide
├── .gitignore                  # VCS ignore definitions (.env and *.db excluded)
├── .env.example                # Sample environment configuration
├── data/                       # Sandboxed workspace for file operations & local DB
│   ├── .gitkeep
│   ├── sample.csv              # Test tabular file
│   └── notes.txt               # Test text file
├── docs/
│   ├── ARCHITECTURE.md         # System design & request lifecycle
│   ├── SECURITY.md             # Security boundaries & safety model
│   ├── DECISIONS.md            # Technical decisions & assumptions log
│   └── PROGRESS_LOG.md         # Milestones, branch tracking, & roadmap
├── src/
│   └── aura/
│       ├── __init__.py         # Package root & version
│       ├── __main__.py         # Entry point for 'python -m aura'
│       ├── app.py              # Interactive REPL & application driver
│       ├── config.py           # Configuration loading & defaults
│       ├── logging_config.py   # Secure structured logging
│       ├── router.py           # Command routing & allowlist
│       ├── safety.py           # Path validation & sandbox enforcement
│       ├── audio/              # Stage 3 Voice I/O
│       │   ├── __init__.py
│       │   ├── stt.py          # Push-to-talk Speech Recognition
│       │   └── tts.py          # Offline Text-to-Speech (pyttsx3)
│       ├── providers/          # Stage 4 Online AI Providers
│       │   ├── __init__.py
│       │   ├── base.py         # BaseLLMProvider interface
│       │   ├── factory.py      # LLM provider factory
│       │   ├── gemini.py       # Google Gemini REST provider
│       │   └── nvidia.py       # NVIDIA NIM REST provider
│       ├── search/             # Stage 5 Web Search Providers
│       │   ├── __init__.py
│       │   ├── base.py         # BaseSearchProvider & SearchResult
│       │   ├── duckduckgo.py   # Zero-key DuckDuckGo search provider
│       │   ├── factory.py      # Search provider factory
│       │   ├── safety.py       # URL validation & prompt injection defense
│       │   └── tavily.py       # Tavily AI Search REST provider
│       ├── tasks/              # Stage 6 Tasks & Reminders
│       │   ├── __init__.py
│       │   ├── db.py           # SQLite persistence manager
│       │   ├── formatters.py   # CLI display formatting
│       │   ├── models.py       # Task & Reminder dataclasses
│       │   ├── scheduler.py    # Background reminder daemon
│       │   └── time_parser.py  # Natural time parsing utilities
│       └── tools/
│           ├── __init__.py
│           ├── basic.py        # Date, time, and help
│           ├── calculator.py   # Safe AST-based calculator (verbal support)
│           ├── documents.py    # Safe text read/write & PDF inspection
│           ├── files.py        # Workspace file listing & glob search
│           └── tabular.py      # Pandas CSV & openpyxl Excel inspection
└── tests/
    ├── test_audio.py          # Voice TTS & STT tests
    ├── test_calculator.py     # Math & verbal expression tests
    ├── test_documents.py      # PDF & text file read/write tests
    ├── test_files.py          # Workspace file search & sandbox tests
    ├── test_providers.py      # Online AI provider & mock integration tests
    ├── test_router.py         # Routing & fallback tests
    ├── test_search.py         # Web search, URL safety & injection tests
    ├── test_tabular.py        # CSV & Excel schema tests
    └── test_tasks.py          # Task DB, reminder scheduler & parser tests
```
