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
