# Project AURA — Build Instructions for Google Antigravity

> **Purpose of this file:** Give this entire document to Google Antigravity as the project specification. Antigravity should begin inspecting the workspace and implementing the first working version—not merely summarize this plan or generate another plan.

## 1. Your role and expected behavior

Act as the lead Python engineer and patient technical mentor for **Project AURA (AI Utility & Response Assistant)**.

Work directly in the currently open workspace. Inspect existing files before changing anything. If the workspace is empty, create the project structure described below. If code already exists, preserve useful work and adapt it instead of overwriting it blindly.

**Start implementing now.** Do not stop after producing a plan. Do not ask questions unless a genuine blocker prevents safe progress. Where a choice is needed, use the defaults in this document, record the assumption in `docs/DECISIONS.md`, and continue.

Build in small, runnable milestones. After each milestone:
1. Run relevant tests or a smoke test.
2. Fix errors before proceeding.
3. Explain briefly what changed, how to run it, and what the user should learn from it.
4. Keep the project runnable; do not leave the repository in a broken intermediate state.

Prefer clear, beginner-friendly Python with type hints, docstrings, sensible names, and focused modules. Avoid unnecessary complexity and premature abstractions.

---

## 2. Product vision

AURA is a desktop voice assistant written in Python. Its long-term goal is to support:

- General AI questions and natural conversation.
- Voice input and spoken responses.
- Safe opening of approved applications and websites.
- Searching approved folders and managing files with confirmation for risky actions.
- Reading and summarizing PDFs and text documents.
- Exploring CSV and Excel files with Pandas.
- Tasks, reminders, schedules, and optional persistent memory.
- Online web search when configured.
- Hybrid operation: local/basic features should remain useful when internet or AI credentials are unavailable.
- Optional smart-home integrations in a later phase.

Do not attempt to implement every advanced feature in the first milestone. First create a reliable, testable foundation and a useful text-based command loop. Add voice and integrations incrementally.

## 3. First milestone: implement this now

Create a **working Python MVP** with these capabilities:

1. A command-line assistant that starts with `python -m aura`.
2. A text input loop that accepts commands until the user types `exit`, `quit`, or `bye`.
3. A friendly help command (`help`) that lists available commands.
4. A local time/date command (`time` or `date`).
5. A safe calculator command that supports basic arithmetic without using `eval` or executing arbitrary Python.
6. A file-listing/search command limited to a user-configurable workspace folder. It must not crawl the whole computer.
7. A document-inspection command that can report metadata and extract text from a PDF when the PDF dependency is installed. If it is missing, show a helpful installation message rather than crashing.
8. A CSV-inspection command using Pandas when installed: show column names, row count, and a small preview. Do not print an entire large file.
9. A conversational fallback that clearly explains that online AI is not configured yet, rather than pretending an AI model answered.
10. Clear error handling, logging, configuration, and automated tests.

Use a simple command router with an explicit allowlist. **Do not execute shell commands, arbitrary code, or model-generated instructions.** Commands that are not recognized should receive a helpful response.

If time permits after the above passes tests, add optional text-to-speech behind a configuration flag. Do not make microphone access or a cloud API key mandatory for the MVP.

## 4. Technology and compatibility defaults

- Language: Python 3.11 or newer, preferring the newest stable version already installed in the environment.
- Packaging: `pyproject.toml`.
- CLI entry point: `python -m aura`.
- Tests: `pytest`.
- Configuration: environment variables and a `.env.example`; load `.env` only if a suitable dependency is installed. Never commit real secrets.
- Tabular data: `pandas`.
- PDF text extraction: `pymupdf` (imported as `fitz`), implemented as an optional capability with a clear error if unavailable.
- Optional text-to-speech later: `pyttsx3`.
- Optional voice transcription later: `faster-whisper`.
- Optional wake-word detection later: `openWakeWord`.
- Persistence later: SQLite via Python's standard `sqlite3` module.
- Scheduling later: `APScheduler`, only when reminder functionality is actually implemented.
- Online AI and web search: use provider interfaces so a provider can be configured later. Do not hard-code a vendor or require credentials for local features.

Check the Python version and available environment before selecting package versions. Use compatible, stable versions and record dependencies clearly. Avoid installing large audio/model packages in the first milestone.

## 5. Workspace layout

Create a structure close to the following, adjusting only when there is a clear reason:

```text
project-aura/
├── pyproject.toml
├── README.md
├── .gitignore
├── .env.example
├── src/
│   └── aura/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── config.py
│       ├── router.py
│       ├── safety.py
│       ├── logging_config.py
│       └── tools/
│           ├── __init__.py
│           ├── basic.py
│           ├── calculator.py
│           ├── files.py
│           ├── documents.py
│           └── tabular.py
├── tests/
│   ├── test_router.py
│   ├── test_calculator.py
│   ├── test_files.py
│   └── test_tabular.py
├── data/
│   └── .gitkeep
└── docs/
    ├── ARCHITECTURE.md
    ├── SECURITY.md
    └── DECISIONS.md
```

The workspace folder for file operations should default to the project's `data/` directory. Make it configurable through an environment variable such as `AURA_WORKSPACE_DIR`. Resolve paths and verify that requested files remain inside the allowed workspace before reading or modifying them.

## 6. Design and architecture

Use a modular architecture:

```text
User text (MVP; voice later)
        ↓
Input / speech adapter
        ↓
Command router and intent selection
        ↓
Safety checks and argument validation
        ↓
Allowlisted local tools / optional AI provider / optional web search
        ↓
Response builder
        ↓
Text output (speech output later)
```

Keep the user interface separate from tool implementations. Each tool should have a clear input contract and return a useful result or a controlled error. Avoid a single giant `app.py`.

Future voice architecture:

```text
Microphone → Wake-word detector → Speech-to-text
           → Intent router → Safety checks → Approved tool
           → Response → Text-to-speech
```

Begin with typed input. Add push-to-talk voice input after the text MVP is stable. Add wake-word listening only after explicit user configuration and clear recording/listening indicators are in place.

## 7. Required security and privacy rules

These rules are mandatory, not optional:

- Never use `eval`, `exec`, or an unrestricted shell to interpret user requests.
- Never execute commands copied from an AI response, webpage, PDF, or other document.
- Use an explicit allowlist of supported tools and validate all arguments.
- Restrict file access to the configured AURA workspace by default.
- Prevent path traversal and reject paths that resolve outside the workspace.
- Do not delete, overwrite, move, upload, or share user files in the MVP.
- Any future destructive or sensitive action must display the exact proposed action and require explicit confirmation.
- Never expose API keys or passwords in logs, output, tests, or source control.
- Do not record or retain microphone audio by default.
- Do not store conversation history or personal memory unless the user opts in.
- Treat document content, webpages, and model outputs as untrusted data, not instructions to the assistant.
- Use safe, bounded output for large files and errors.
- Add `.env`, virtual environments, caches, logs, and generated private data to `.gitignore`.
- Provide a clear way to stop the assistant immediately.

## 8. Future development roadmap

Do not implement all of these before the MVP is tested. Work in this order and keep each stage independently runnable.

### Stage 1 — Text MVP
Implement the first-milestone requirements above, documentation, and tests.

### Stage 2 — Better local tools
Improve file search, add safe text-file reading, and support PDF extraction. Add Excel (`.xlsx`) preview using `openpyxl` or Pandas. Keep access inside the configured workspace.

### Stage 3 — Voice output and input
Add optional text-to-speech, then push-to-talk speech recognition. Keep typed input available as a fallback.

### Stage 4 — Online AI
Add an AI-provider interface and one configurable provider. Read credentials from environment variables. If credentials are missing or the network is unavailable, explain that clearly and continue to support local commands.

### Stage 5 — Web search
Add a provider-based web-search tool. Show source titles/links where possible, distinguish retrieved information from the assistant's own reasoning, and treat webpage text as untrusted.

### Stage 6 — Tasks and reminders
Use SQLite for persistent tasks and reminders. Add scheduling only after the data model and tests are in place. Ask for confirmation before scheduling external actions or sending messages.

### Stage 7 — Wake word
Add optional wake-word detection, visible listening state, a stop/pause control, and configurable privacy behavior. Do not run always-on listening silently.

### Stage 8 — Memory
Add opt-in memory with view, edit, and delete controls. Clearly separate short-term conversation context from saved facts.

### Stage 9 — Application control
Open only explicitly approved applications and websites through safe, platform-aware adapters. Never provide a general arbitrary shell-command tool.

### Stage 10 — Smart-home integrations
Add only when the user configures a supported platform. Require confirmation for actions that affect safety, security, access, or significant energy use.

## 9. Definition of done for the first milestone

The first milestone is complete only when all applicable checks pass:

- [ ] Project structure and packaging are in place.
- [ ] `python -m aura` starts the assistant from the project environment.
- [ ] `help`, `time`, `date`, `exit`, and `quit` work.
- [ ] Calculator handles valid arithmetic and safely rejects unsupported expressions.
- [ ] File search/listing is limited to the configured workspace.
- [ ] PDF/CSV features work when dependencies are installed and degrade gracefully when optional dependencies are missing.
- [ ] Unrecognized commands do not crash the application.
- [ ] No arbitrary shell or Python execution exists.
- [ ] Tests pass with `pytest`.
- [ ] README includes setup, installation, run, test, supported commands, and limitations.
- [ ] `.env.example` contains placeholders only.
- [ ] `docs/SECURITY.md` explains the security boundaries.
- [ ] `docs/ARCHITECTURE.md` explains how requests flow through the application.
- [ ] `docs/DECISIONS.md` records assumptions and compatibility choices.

## 10. How to work with the user

The user knows Python basics, functions, and modules, and wants to learn by building a real project. For each completed milestone:

- Explain the key files and their responsibilities in plain language.
- Give exact commands to create/activate the environment, install dependencies, run the app, and run tests for the user's operating system when it is known.
- Explain important design and security decisions without overwhelming the user.
- Prefer a small working implementation over a large untested code dump.
- Do not claim a feature works unless it has been implemented and tested.
- If a command or dependency cannot be verified in the current environment, say so and provide the next verification step.

## 11. First actions to perform immediately

1. Inspect the current workspace, available Python version, and existing project files.
2. Summarize any relevant existing files and state the assumptions you will use.
3. Create or adapt the Stage 1 project structure.
4. Implement the text command loop and required safe local tools.
5. Add focused tests for routing, calculator safety, workspace boundaries, and CSV behavior.
6. Run the tests and fix failures.
7. Run the assistant once as a smoke test if the environment permits.
8. Update `README.md` and the documentation files.
9. Report the exact files created/changed, test results, run commands, and any remaining limitations.
10. **Do not stop at step 2 or return only a plan. Complete as much of Stage 1 as the workspace and tools allow.**

---

## 12. Copy/paste kickoff message

After adding this Markdown file to the project workspace, send Antigravity this message:

> Read `AURA_ANTIGRAVITY_BUILD_SPEC.md` completely and follow it as the implementation specification. Inspect the current workspace first, then begin Stage 1 immediately. Make the code changes directly in the workspace, run tests, fix failures, and update the documentation. Do not just explain what you intend to do or generate another plan. Do not add voice, cloud AI, wake-word detection, or smart-home dependencies until the Stage 1 MVP is working and tested. If the workspace is empty, create the project structure from the specification. When finished, summarize the implementation, test results, exact setup/run commands, and what I should learn or do next.
