"""Security constraints, workspace boundary validation, and sanitization."""

from __future__ import annotations

from pathlib import Path


class SecurityError(Exception):
    """Raised when an operation violates security boundaries."""


def validate_workspace_path(requested_path: str | Path, workspace_dir: Path) -> Path:
    """Validate that a requested path stays strictly within the workspace directory.

    Rejects directory traversal attacks (e.g. `../../etc/passwd` or `C:\\Windows`).
    Returns the resolved, safe Path.
    """
    if not requested_path:
        raise SecurityError("Path cannot be empty.")

    base_dir = workspace_dir.resolve()
    target_path = Path(requested_path)

    # If relative, anchor to base_dir; if absolute, resolve directly
    if not target_path.is_absolute():
        resolved_path = (base_dir / target_path).resolve()
    else:
        resolved_path = target_path.resolve()

    # Check whether resolved path is inside base_dir or is base_dir itself
    try:
        resolved_path.relative_to(base_dir)
    except ValueError:
        raise SecurityError(
            f"Access denied: '{requested_path}' escapes the workspace boundary ({base_dir})."
        )

    return resolved_path


def sanitize_output(text: str, max_chars: int = 4000) -> str:
    """Truncate overly large output to prevent terminal flooding."""
    if len(text) > max_chars:
        return text[:max_chars] + f"\n... [Output truncated to {max_chars} characters]"
    return text
