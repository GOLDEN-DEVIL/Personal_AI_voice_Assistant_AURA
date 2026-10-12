"""Command router and allowlisted intent execution."""

from __future__ import annotations

import re
from typing import Tuple

from aura.config import AuraConfig
from aura.tools.basic import format_help, get_current_date, get_current_time
from aura.tools.calculator import evaluate_expression
from aura.tools.documents import inspect_pdf, read_text_file
from aura.tools.files import list_workspace_files, search_workspace_files
from aura.tools.tabular import inspect_csv


class CommandRouter:
    """Routes user input to allowlisted local tools or safe fallbacks."""

    def __init__(self, config: AuraConfig) -> None:
        self.config = config
        self.command_help: dict[str, str] = {
            "help": "Display this help menu with all available commands",
            "time": "Show current local time and timezone",
            "date": "Show current date and day of week",
            "calc <expr>": "Safely compute math (e.g. 'calc (25 * 4) + sqrt(16)')",
            "files [folder]": "List files inside the workspace (or a subfolder)",
            "search <pattern>": "Search workspace files matching pattern (e.g. 'search *.csv')",
            "read <filename>": "Safely read and preview a text document from workspace",
            "csv <filename>": "Inspect CSV structure, columns, and data preview via Pandas",
            "pdf <filename>": "Inspect PDF metadata and page text via PyMuPDF",
            "exit / quit / bye": "Terminate the assistant session",
        }

    def execute(self, user_input: str) -> Tuple[str, bool]:
        """Parse and execute a command.

        Returns:
            Tuple of (response_message, should_exit_flag)
        """
        trimmed = user_input.strip()
        if not trimmed:
            return "Please enter a command. Type 'help' for a list of available commands.", False

        parts = trimmed.split(maxsplit=1)
        command_key = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        # Session termination commands
        if command_key in ("exit", "quit", "bye", "q"):
            return "Goodbye! Have a productive day.", True

        # Help
        if command_key in ("help", "?"):
            return format_help(self.command_help), False

        # Time & Date
        if command_key == "time":
            return get_current_time(), False

        if command_key == "date":
            return get_current_date(), False

        # Safe Calculator
        if command_key in ("calc", "calculate", "math"):
            if not args:
                return "Usage: calc <expression> (e.g., 'calc 100 / (4 + 6)' or 'calc sqrt(144)')", False
            return evaluate_expression(args), False

        # Workspace File Listing
        if command_key in ("files", "list", "ls", "dir"):
            return list_workspace_files(self.config.workspace_dir, args), False

        # Workspace File Search
        if command_key in ("search", "find"):
            if not args:
                return "Usage: search <pattern> (e.g., 'search *.csv' or 'search sample')", False
            return search_workspace_files(self.config.workspace_dir, args), False

        # Read Text File
        if command_key in ("read", "cat", "view"):
            if not args:
                return "Usage: read <filename> (e.g., 'read notes.txt')", False
            return read_text_file(
                self.config.workspace_dir,
                args,
                max_chars=self.config.max_preview_chars,
            ), False

        # CSV Data Inspection
        if command_key in ("csv", "table", "dataframe"):
            if not args:
                return "Usage: csv <filename> (e.g., 'csv sample.csv')", False
            return inspect_csv(
                self.config.workspace_dir,
                args,
                preview_rows=self.config.max_preview_rows,
            ), False

        # PDF Inspection
        if command_key in ("pdf", "document"):
            if not args:
                return "Usage: pdf <filename> (e.g., 'pdf report.pdf')", False
            return inspect_pdf(
                self.config.workspace_dir,
                args,
                max_chars=self.config.max_preview_chars,
            ), False

        # Conversational / AI fallback check
        if self._is_conversational(trimmed):
            return (
                "AURA is currently operating in local-only mode (Stage 1 MVP).\n"
                "Online AI and cloud language models are not configured yet.\n"
                "Local features (files, calculation, CSV preview, date/time) are fully active.\n"
                "Type 'help' to see what I can do locally.",
                False,
            )

        # Unrecognized command
        return (
            f"Unrecognized command: '{command_key}'.\n"
            f"Type 'help' to view the list of supported commands or 'exit' to quit.",
            False,
        )

    def _is_conversational(self, text: str) -> bool:
        """Detect conversational questions or natural language queries."""
        lowered = text.lower()
        conversational_patterns = [
            r"^(hi|hello|hey|howdy|greetings)\b",
            r"^(who|what|why|where|when|how|can you|could you|tell me|explain|write|generate)\b",
            r"^(are you|do you have|what's your name|who made you)\b",
        ]
        return any(re.search(pat, lowered) for pat in conversational_patterns)
