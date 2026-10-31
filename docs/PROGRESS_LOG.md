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

## Next Milestone: Stage 5 — Provider-Based Web Search
- Web search provider tool returning concise source titles and links.
- Clearly separate retrieved search text from assistant reasoning.
- Treat untrusted web results with prompt injection safeguards.
