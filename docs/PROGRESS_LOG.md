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

### Stage 4: Online AI Provider Integration (Branch `TEST_STAGE_4`)
- **Pluggable Provider Architecture** ([`src/aura/providers/base.py`](../src/aura/providers/base.py)):
  - Abstract `BaseLLMProvider` interface defining availability checks, model identification, and response generation.
- **Google Gemini Provider** ([`src/aura/providers/gemini.py`](../src/aura/providers/gemini.py)):
  - Built-in HTTPS REST interface using Python standard library `urllib.request` (zero third-party package friction).
  - Configurable models (`gemini-1.5-flash`, `gemini-2.0-flash`) via `AURA_AI_MODEL`.
  - Automatic error handling for missing keys, HTTP 403 (invalid key), HTTP 429 (rate limits/quota), and network outages.
- **Router & CLI Integration** ([`src/aura/router.py`](../src/aura/router.py), [`src/aura/app.py`](../src/aura/app.py)):
  - `ask <prompt>` / `ai <prompt>` explicit query commands.
  - Conversational routing that forwards natural questions to Gemini when configured.
  - Local tools (`calc`, `files`, `excel`, `pdf`, `voice`) remain 100% operational when offline or unauthenticated.
  - Live AI status indicator in terminal startup banner.
- **Automated Tests**: 55 unit and security tests passing.

---

## Next Milestone: Stage 5 — Provider-Based Web Search
- Web search provider tool returning concise source titles and links.
- Clearly separate retrieved search text from assistant reasoning.
- Treat untrusted web results with prompt injection safeguards.

