# Project AURA — Architecture & Design Decisions Log

This document records key technical decisions, assumptions, and trade-offs made during development.

---

### Decision 1: Text-Based REPL for Stage 1 MVP
- **Context**: The full vision includes voice input (Whisper), wake-word detection, and text-to-speech.
- **Decision**: Deliver a complete text-first CLI loop (`python -m aura`) before integrating audio libraries.
- **Rationale**: Audio hardware requirements (microphones, native C/C++ audio drivers like PyAudio) frequently cause platform-specific dependency failures. A stable text foundation enables automated testing and guaranteed reliability across all OS environments.

---

### Decision 2: AST-Based Mathematical Evaluation
- **Context**: Users expect arithmetic calculations (`calc 25 * 4`, `calc sqrt(16)`).
- **Decision**: Implement a custom AST visitor with an explicit allowlist of nodes rather than calling `eval()` or importing heavy third-party CAS libraries.
- **Rationale**: `eval()` in Python is vulnerable to code injection. The AST approach allows exact control over permitted mathematical operations while guaranteeing zero access to system calls, attributes, or builtins.

---

### Decision 3: Sandbox Workspace Folder
- **Context**: Users want file inspection and search without risking unauthorized disk access.
- **Decision**: Bind all file operations to a configurable workspace directory (`AURA_WORKSPACE_DIR`, defaulting to `AI_voice_assistant_AURA/data`).
- **Rationale**: Restricting access to a specific folder prevents accidental exposure or modification of sensitive operating system files and parent user directories.

---

### Decision 4: Graceful Degradation for Optional Dependencies
- **Context**: PDF inspection requires `pymupdf` (`fitz`), which might not be installed in minimal environments.
- **Decision**: Catch `ImportError` gracefully and return an actionable installation instruction (`pip install pymupdf`) rather than crashing the program.
- **Rationale**: Ensures the core assistant remains fully functional even in constrained environments.

---

### Decision 5: Explicit Command Router Allowlist
- **Context**: Need to route user queries without risking prompt injection or unauthorized function calls.
- **Decision**: Use a dictionary-backed allowlist in `CommandRouter`. Check conversational intent using regex patterns to provide informative guidance when online LLMs are not yet hooked up.
- **Rationale**: Predictable, robust, and zero-overhead execution without relying on an external model to interpret fundamental assistant commands.

---

### Decision 6: Excel Workbook Multi-Sheet Support
- **Context**: Users need to explore spreadsheet data (`.xlsx`) with multiple sheets without loading giant files into terminal memory.
- **Decision**: Use `openpyxl` with Pandas `ExcelFile` to inspect available sheets, parse targeted sheets on demand, and bound output previews to top-N rows.
- **Rationale**: Memory-safe inspection with clear visibility into multi-tab workbooks.

---

### Decision 7: Safe File Writing with Accidental Overwrite Protection
- **Context**: In Stage 2, users want note-taking and text-file creation within the workspace.
- **Decision**: Restrict write capabilities to non-executable extensions (`.txt`, `.md`, `.log`, `.csv`, `.json`). If a file already exists, require `--overwrite` or explicit `append` rather than silently replacing content.
- **Rationale**: Upholds the core security rule that assistant actions must not destroy user data without explicit consent.

---

### Decision 8: Offline Text-to-Speech (TTS) with Speech Filtering
- **Context**: Users want voice responses spoken aloud without relying on external cloud APIs or high network latency.
- **Decision**: Use `pyttsx3` operating over native OS speech synthesizers (`sapi5` on Windows). Implement a regex speech sanitizer (`clean_text_for_speech`) that filters out ASCII dividers, table borders, and truncates lengthy text before passing to the audio engine.
- **Rationale**: Guarantees zero cloud cost, 100% offline privacy, and natural spoken output that avoids reading raw table borders aloud.

---

### Decision 9: Push-to-Talk Speech Recognition with Zero Audio Retention
- **Context**: Voice input is needed while preserving keyboard fallback and strict user privacy.
- **Decision**: Use push-to-talk speech recognition activated by user command (`listen`). Never record, stream, or retain audio to local disk files.
- **Rationale**: Complies directly with Section 7 security and privacy rules while avoiding constant, silent background listening.

---

### Decision 10: Pluggable Online AI Architecture with Standard Library HTTPS
- **Context**: Stage 4 introduces cloud LLMs for answering freeform conversational questions. We need support for Google Gemini without fragile package compilation or heavy third-party dependencies.
- **Decision**: Implemented `BaseLLMProvider` interface and `GeminiProvider` using Python's standard library `urllib.request` over the official Gemini REST API (`generateContent`).
- **Rationale**: Zero external package friction on Python 3.13, no complex build wheels, fast HTTPS calls, and robust error handling for missing keys, HTTP 403, and HTTP 429 quota exhaustion while preserving local tools.
