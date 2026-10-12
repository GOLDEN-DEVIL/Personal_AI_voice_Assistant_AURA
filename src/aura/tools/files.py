"""Workspace-bounded file listing and search tools."""

from __future__ import annotations

from pathlib import Path
from typing import List

from aura.safety import SecurityError, validate_workspace_path


def format_size(num_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def list_workspace_files(workspace_dir: Path, subpath: str = "") -> str:
    """List files and folders within the workspace directory, preventing traversal."""
    try:
        target_dir = validate_workspace_path(subpath if subpath else ".", workspace_dir)
    except SecurityError as err:
        return f"Security Error: {err}"

    if not target_dir.exists():
        return f"Error: Directory '{subpath}' does not exist inside workspace."

    if not target_dir.is_dir():
        return f"Error: '{subpath}' is a file, not a directory. Use 'read {subpath}' to inspect its content."

    try:
        entries = sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return f"Permission Error: Cannot read contents of '{target_dir.name}'."

    if not entries:
        return f"Workspace directory '{target_dir.relative_to(workspace_dir)}' is empty."

    lines: List[str] = [
        f"Contents of '{target_dir.relative_to(workspace_dir)}' ({len(entries)} items):",
        f"{'TYPE':<6} {'SIZE':<12} {'NAME'}",
        "-" * 45,
    ]

    # Limit maximum displayed entries to keep terminal clean
    max_items = 50
    for entry in entries[:max_items]:
        if entry.is_dir():
            lines.append(f"{'[DIR]':<6} {'-':<12} {entry.name}/")
        else:
            size_str = format_size(entry.stat().st_size)
            lines.append(f"{'[FILE]':<6} {size_str:<12} {entry.name}")

    if len(entries) > max_items:
        lines.append(f"... ({len(entries) - max_items} more items not shown)")

    return "\n".join(lines)


def search_workspace_files(workspace_dir: Path, pattern: str) -> str:
    """Search for files matching a glob pattern inside the workspace directory.

    Supports optional type filters:
      search *.csv
      search sample --files
      search reports --dirs
    """
    clean_input = pattern.strip()
    if not clean_input:
        return "Error: Please specify a search pattern (e.g., 'search *.csv' or 'search sample --files')."

    # Block directory traversal attempts in search pattern
    if ".." in clean_input or clean_input.startswith(("/", "\\")):
        return "Security Error: Search pattern must not contain traversal characters ('..' or absolute paths)."

    tokens = clean_input.split()
    type_filter = None  # None, "file", or "dir"
    clean_parts = []

    for token in tokens:
        if token in ("--files", "--file", "-f"):
            type_filter = "file"
        elif token in ("--dirs", "--dir", "-d"):
            type_filter = "dir"
        else:
            clean_parts.append(token)

    query = " ".join(clean_parts).strip()
    if not query:
        query = "*"

    # If simple text without glob wildcards, search substring
    glob_pattern = f"*{query}*" if not any(c in query for c in "*?[]") else query

    matches: List[Path] = []
    try:
        for p in workspace_dir.rglob(glob_pattern):
            try:
                # Ensure each match is inside workspace
                validate_workspace_path(p, workspace_dir)
                if type_filter == "file" and not p.is_file():
                    continue
                if type_filter == "dir" and not p.is_dir():
                    continue
                matches.append(p)
            except SecurityError:
                continue
    except Exception as err:
        return f"Search Error: {err}"

    if not matches:
        filter_msg = f" (filtered by {type_filter})" if type_filter else ""
        return f"No matching items found for pattern: '{query}'{filter_msg}"

    filter_desc = f" [{type_filter}s only]" if type_filter else ""
    lines = [f"Found {len(matches)} match(es) for '{query}'{filter_desc}:"]
    for match in matches[:40]:
        rel = match.relative_to(workspace_dir)
        tag = "[DIR] " if match.is_dir() else "[FILE]"
        lines.append(f"  {tag} {rel}")

    if len(matches) > 40:
        lines.append(f"  ... ({len(matches) - 40} additional matches truncated)")

    return "\n".join(lines)
