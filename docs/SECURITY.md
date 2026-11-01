# Project AURA — Security & Privacy Boundaries

Security and privacy are core tenets of Project AURA. This document outlines the security architecture, threat model, and design rules implemented in the project.

## 1. Core Security Principles

### No Dynamic Code or Shell Execution
- **Zero `eval` / `exec`**: User expressions are never evaluated using Python's `eval()` or `exec()`.
- **Zero Subprocess / Shell execution**: AURA does not execute raw shell commands (`os.system`, `subprocess.Popen`) based on user input or model output.
- **AST-Based Math Parser**: Arithmetic calculations are validated through Python's `ast` module (`ast.parse(expr, mode='eval')`). Only strictly allowlisted mathematical operations, constants (`pi`, `e`), and functions (`sqrt`, `abs`, etc.) are processed. All attribute access (`obj.attr`), function definitions, loops, and arbitrary calls are strictly blocked.

### Workspace Sandbox & Path Traversal Prevention
- All file system operations (`files`, `search`, `read`, `write`, `append`, `csv`, `excel`, `pdf`) are strictly confined to the configured workspace directory (`AURA_WORKSPACE_DIR`, defaults to `./data`).
- `aura.safety.validate_workspace_path` resolves canonical paths and validates `resolved_path.relative_to(base_dir)`.
- Path traversal sequences (`../`, absolute system drives like `C:\Windows`) raise an immediate `SecurityError` and are rejected before any disk access occurs.

### Safe Write & Append Controls (Stage 2)
- Note and document creation is restricted to safe text file extensions (`.txt`, `.md`, `.log`, `.csv`, `.json`). Executable extensions (`.exe`, `.bat`, `.py`) are denied.
- Overwriting existing files requires the explicit `--overwrite` flag. Otherwise, modifications must use `append`.

### Zero Audio Retention & Privacy First (Stage 3)
- Microphone recording operates strictly on a **push-to-talk** basis (`listen` / `ptt`).
- Audio is captured in-memory for immediate transcription and is **never written to disk, saved in logs, or retained**.
- Offline Text-to-Speech (TTS) runs completely locally via native OS drivers (`sapi5`/`espeak`) with no third-party cloud data transmission.

### Secret Credentials & API Key Handling (Stage 4)
- API keys (`NVIDIA_API_KEY`, `GEMINI_API_KEY`) are read exclusively from environment variables via `.env`.
- `.env` is permanently excluded from version control via `.gitignore`.
- Keys are masked in application logs and diagnostic outputs to prevent credential leaks.
- Outbound AI queries are sent over secure HTTPS REST endpoints with strict timeout bounds.

### Bounded Output & Resource Exhaustion Defense
- File readings and document extractions are bounded (default max 2000 characters) to prevent terminal flooding or memory exhaustion.
- Tabular previews are capped (default top 5 rows) instead of loading and printing entire gigabyte-scale datasets.
- Large numerical powers in calculations (`base ** exponent` with `abs(exponent) > 1000`) are rejected before execution to avoid CPU hang.

### Untrusted Content Isolation
- External documents (PDF, text, CSV, Excel) and online AI completions are treated strictly as **untrusted data**, never as executable instructions or system prompts.


### Web Search & Prompt Injection Defense (Stage 5)
- **Strict URL Scheme Allowlist**: All URLs returned from web searches must strictly resolve to `http://` or `https://` schemes. Potentially dangerous schemes (`javascript:`, `file:`, `data:`, `vbscript:`, `blob:`) and URLs containing unprintable control characters or null bytes are rejected immediately by `aura.search.safety.validate_url`.
- **Character Bounding**: Web snippets (max 400 chars) and titles (max 150 chars) are strictly truncated and stripped of raw HTML to prevent buffer overflows or terminal flooding.
- **Indirect Prompt Injection Neutralization**: External web text is scanned for adversarial prompt-override patterns (e.g., `Ignore previous instructions`, `### System:`, `[INST]`, `you are now in developer mode`). Matching sequences are defanged into unverified quoted tokens (`[defanged: '...']`).
- **LLM Sandboxing & Context Isolation**: For grounded queries (`webask`), retrieved search excerpts are wrapped in strict `<unverified_external_web_search_results>` XML tags, instructing the AI to treat them exclusively as external reference data and never as executable instructions.
