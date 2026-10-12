# Project AURA — Security & Privacy Boundaries

Security and privacy are core tenets of Project AURA. This document outlines the security architecture, threat model, and design rules implemented in the MVP.

## 1. Core Security Principles

### No Dynamic Code or Shell Execution
- **Zero `eval` / `exec`**: User expressions are never evaluated using Python's `eval()` or `exec()`.
- **Zero Subprocess / Shell execution**: AURA does not execute raw shell commands (`os.system`, `subprocess.Popen`) based on user input or model output.
- **AST-Based Math Parser**: Arithmetic calculations are validated through Python's `ast` module (`ast.parse(expr, mode='eval')`). Only strictly allowlisted mathematical operations, constants (`pi`, `e`), and functions (`sqrt`, `abs`, etc.) are processed. All attribute access (`obj.attr`), function definitions, loops, and arbitrary calls are strictly blocked.

### Workspace Sandbox & Path Traversal Prevention
- All file system operations (`files`, `search`, `read`, `csv`, `pdf`) are confined to the configured workspace directory (defaults to `./data`).
- `aura.safety.validate_workspace_path` resolves canonical paths and validates `resolved_path.relative_to(base_dir)`.
- Path traversal sequences (`../`, absolute system drives like `C:\Windows`) raise an immediate `SecurityError` and are rejected before any disk access occurs.

### Read-Only in MVP
- The MVP operates exclusively in **read-only mode** on the local filesystem.
- No files can be created, updated, overwritten, moved, or deleted through assistant commands.
- Destructive operations in future stages will require mandatory explicit user confirmation.

### Bounded Output & Resource Exhaustion Defense
- File readings and document extractions are bounded (default max 2000 characters) to prevent terminal flooding or memory exhaustion.
- Tabular previews are capped (default top 5 rows) instead of loading and printing entire gigabyte-scale datasets.
- Large numerical powers in calculations (`base ** exponent` with `abs(exponent) > 1000`) are rejected before execution to avoid CPU hang.

### Untrusted Content Isolation
- Documents (PDF, text, CSV) and future model outputs are treated strictly as **untrusted data**, never as executable instructions or system prompts.

### Privacy & Data Protection
- Microphone recording, continuous audio retention, and persistent profiling are disabled by default.
- Secret credentials (such as API keys) must only be passed through environment variables and are never checked into version control.
