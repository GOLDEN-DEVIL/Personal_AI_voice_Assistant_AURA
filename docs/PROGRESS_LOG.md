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

## Next Milestone: Stage 4 — Online AI Provider Integration
- Configurable LLM provider interface (`src/aura/providers/`).
- Connect cloud model (e.g., Google Gemini API, Groq, or local Ollama).
- Clear fallback to local tools if network or API keys are unavailable.
