"""Command router and allowlisted intent execution."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from aura.audio.tts import TextToSpeechEngine
from aura.config import AuraConfig
from aura.providers.base import BaseLLMProvider
from aura.search.base import BaseSearchProvider
from aura.search.safety import (
    format_search_context_for_llm,
    format_search_results_for_display,
)
from aura.tasks.db import TaskDatabase
from aura.tasks.formatters import format_reminders_list, format_tasks_list
from aura.tasks.time_parser import parse_reminder_command
from aura.tools.basic import format_help, get_current_date, get_current_time
from aura.tools.calculator import evaluate_expression
from aura.tools.documents import inspect_pdf, read_text_file, write_text_file
from aura.tools.files import list_workspace_files, search_workspace_files
from aura.tools.tabular import inspect_csv, inspect_excel


class CommandRouter:
    """Routes user input to allowlisted local tools or safe fallbacks."""

    def __init__(
        self,
        config: AuraConfig,
        tts_engine: Optional[TextToSpeechEngine] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        search_provider: Optional[BaseSearchProvider] = None,
        task_db: Optional[TaskDatabase] = None,
    ) -> None:
        self.config = config
        self.tts = tts_engine
        self.llm = llm_provider
        self.search = search_provider
        self.task_db = task_db
        self.command_help: dict[str, str] = {
            "help": "Display this help menu with all available commands",
            "time": "Show current local time and timezone",
            "date": "Show current date and day of week",
            "calc <expr>": "Safely compute math (e.g. 'calc (25 * 4) + sqrt(16)')",
            "files [folder]": "List files inside the workspace (or a subfolder)",
            "search <pattern>": "Search workspace files matching pattern (e.g. 'search *.csv --files')",
            "read <filename>": "Safely read and preview a text document from workspace",
            "write <file> <text>": "Safely create a new text file or note in workspace",
            "append <file> <text>": "Safely append content to an existing text file",
            "csv <filename>": "Inspect CSV structure, columns, and data preview via Pandas",
            "excel <file> [sheet]": "Inspect Excel spreadsheet workbook and sheet contents via openpyxl",
            "pdf <filename>": "Inspect PDF metadata and page text via PyMuPDF",
            "task [add|list|done|delete]": "Manage persistent tasks (e.g. 'task add Finish slides --priority high')",
            "remind <when> to <msg>": "Schedule a timed reminder (e.g. 'remind in 15m to take a break')",
            "reminders": "List scheduled reminders or use 'reminder cancel <id>'",
            "voice [on/off]": "Toggle or check spoken audio responses (Text-to-Speech)",
            "listen": "Activate push-to-talk microphone to speak your command",
            "ask <question>": "Ask conversational AI anything (requires NVIDIA_API_KEY in .env)",
            "web <query>": "Search live web and display cited sources, titles, and links",
            "webask <query>": "Search web and synthesize answer with source citations via AI",
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
                return "Usage: search <pattern> (e.g., 'search *.csv' or 'search notes --files')", False
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

        # Write Text File / Note
        if command_key in ("write", "note", "save"):
            if not args:
                return "Usage: write <filename> [--overwrite] <content> (e.g., 'write notes.txt Meeting notes')", False
            arg_tokens = args.split(maxsplit=2)
            filename = arg_tokens[0]
            overwrite = False
            content = ""

            if len(arg_tokens) > 1 and arg_tokens[1] == "--overwrite":
                overwrite = True
                content = arg_tokens[2] if len(arg_tokens) > 2 else ""
            else:
                content = args[len(filename):].strip()

            if not content:
                return f"Error: Content to write cannot be empty. Usage: write {filename} <content>", False

            return write_text_file(
                self.config.workspace_dir,
                filename,
                content,
                overwrite=overwrite,
            ), False

        # Append Text File / Note
        if command_key in ("append", "add"):
            if not args:
                return "Usage: append <filename> <content> (e.g., 'append notes.txt New bullet point')", False
            arg_tokens = args.split(maxsplit=1)
            filename = arg_tokens[0]
            content = arg_tokens[1] if len(arg_tokens) > 1 else ""

            if not content:
                return f"Error: Content to append cannot be empty. Usage: append {filename} <content>", False

            return write_text_file(
                self.config.workspace_dir,
                filename,
                content,
                append=True,
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

        # Excel Data Inspection
        if command_key in ("excel", "xlsx", "sheet", "sheets"):
            if not args:
                return "Usage: excel <filename> [sheet] (e.g., 'excel sample.xlsx' or 'excel sales.xlsx Q1')", False
            arg_tokens = args.split(maxsplit=1)
            filename = arg_tokens[0]
            sheet = arg_tokens[1] if len(arg_tokens) > 1 else None
            return inspect_excel(
                self.config.workspace_dir,
                filename,
                sheet_name=sheet,
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

        # Tasks Management (Stage 6)
        if command_key in ("task", "tasks", "todo"):
            return self._handle_task_command(args), False

        # Reminders Management (Stage 6)
        if command_key in ("remind", "reminder", "reminders"):
            return self._handle_reminder_command(command_key, args), False

        # Voice Output (TTS) Controls
        if command_key in ("voice", "tts"):
            sub_cmd = args.strip().lower()
            if sub_cmd in ("on", "enable", "start", "1"):
                if self.tts:
                    self.tts.set_enabled(True)
                    return "Voice output (Text-to-Speech) is now ENABLED.", False
                return "Voice output engine is not initialized in this session.", False
            elif sub_cmd in ("off", "disable", "stop", "0"):
                if self.tts:
                    self.tts.set_enabled(False)
                    return "Voice output (Text-to-Speech) is now DISABLED.", False
                return "Voice output engine is not initialized in this session.", False
            elif sub_cmd in ("status", ""):
                state = "ENABLED" if (self.tts and self.tts.enabled) else "DISABLED"
                avail = "available" if (self.tts and self.tts.available) else "unavailable"
                return (
                    f"Voice output (TTS) is currently {state} (audio driver: {avail}).\n"
                    "Use 'voice on' or 'voice off' to toggle spoken responses.",
                    False,
                )
            else:
                return "Usage: voice [on|off|status] or tts [on|off|status]", False

        # Push-to-Talk Command
        if command_key in ("listen", "ptt", "mic"):
            return (
                "Push-to-talk microphone trigger received.\n"
                "(In the interactive terminal session, typing 'listen' activates the microphone).",
                False,
            )

        # Web Search Command (Stage 5)
        if command_key in ("web", "websearch", "google", "ddg"):
            if not args:
                return "Usage: web <query> (e.g. 'web latest space missions' or 'web python 3.13 features')", False
            if self.search:
                results = self.search.search(args, max_results=self.config.search_max_results)
                return format_search_results_for_display(results, args), False
            return "Web search provider is not initialized.", False

        # Web Search + AI Synthesis Command (Stage 5)
        if command_key in ("webask", "askweb", "searchask"):
            if not args:
                return "Usage: webask <question> (e.g. 'webask who won the 2024 Nobel Prize in Physics?')", False
            if not self.search:
                return "Web search provider is not initialized.", False

            results = self.search.search(args, max_results=self.config.search_max_results)
            if not results:
                return f"No web search results found for: '{args}'. Unable to ground response.", False

            if not self.llm or not self.llm.is_available():
                results_text = format_search_results_for_display(results, args)
                return (
                    f"AI Notice: Online AI provider is not enabled.\n"
                    f"Retrieved these raw web results without AI synthesis:\n\n{results_text}"
                ), False

            context = format_search_context_for_llm(results, args)
            augmented_prompt = (
                f"{context}\n\n"
                f"User Question: {args}\n\n"
                f"Instructions: Answer the question concisely using the sources above. "
                f"Cite relevant source numbers like [1], [2] when stating facts."
            )
            ai_response = self.llm.generate_response(augmented_prompt)

            citations = "\n\nSources Cited:\n" + "\n".join(
                f"[{i}] {r.title} - {r.url}" for i, r in enumerate(results, start=1)
            )
            return ai_response + citations, False

        # Explicit AI Ask Command
        if command_key in ("ask", "ai", "nvidia", "nim", "gemini"):
            if not args:
                return "Usage: ask <your question or prompt> (e.g. 'ask explain photosynthesis in 2 sentences')", False
            if self.llm:
                return self.llm.generate_response(args), False
            return (
                "AI Notice: Online AI provider is not enabled.\n"
                "Please configure NVIDIA_API_KEY in your .env file to enable AI answers.",
                False,
            )

        # Conversational / AI fallback check
        if self._is_conversational(trimmed):
            if self.llm and self.llm.is_available():
                return self.llm.generate_response(trimmed), False
            return (
                "AURA is currently operating in local-only mode.\n"
                "To enable online conversational AI, add your API key to .env:\n"
                "  NVIDIA_API_KEY=nvapi-your_key_here\n"
                "(Get a free key at https://build.nvidia.com).\n"
                "Type 'help' to see available local tools.",
                False,
            )

        # Unrecognized command
        return (
            f"Unrecognized command: '{command_key}'.\n"
            f"Type 'help' to view the list of supported commands or 'exit' to quit.",
            False,
        )

    # -----------------------------------------------------------------------
    # Task & Reminder Handlers (Stage 6)
    # -----------------------------------------------------------------------

    def _handle_task_command(self, args: str) -> str:
        """Process 'task' and 'tasks' subcommands."""
        if not self.task_db:
            return "Task management database is not initialized."

        trimmed = args.strip()
        if not trimmed or trimmed.lower() in ("list", "ls", "all"):
            tasks = self.task_db.list_tasks()
            return format_tasks_list(tasks)

        tokens = trimmed.split(maxsplit=1)
        sub_cmd = tokens[0].lower()
        sub_args = tokens[1].strip() if len(tokens) > 1 else ""

        # task list [--pending|--done|--completed|--high|--low]
        if sub_cmd in ("list", "ls"):
            status_filter = None
            priority_filter = None
            for flag in sub_args.split():
                f_clean = flag.lower().lstrip("-")
                if f_clean in ("pending", "todo"):
                    status_filter = "pending"
                elif f_clean in ("done", "completed"):
                    status_filter = "completed"
                elif f_clean in ("low", "medium", "high"):
                    priority_filter = f_clean
            tasks = self.task_db.list_tasks(status=status_filter, priority=priority_filter)
            return format_tasks_list(tasks, filter_name=status_filter or priority_filter)

        # task add <title> [--priority low|med|high] [--due YYYY-MM-DD]
        if sub_cmd == "add":
            if not sub_args:
                return "Usage: task add <title> [--priority low|medium|high] [--due YYYY-MM-DD]"

            # Parse optional flags
            priority = "medium"
            due_date = None
            title_parts: list[str] = []
            skip_next = False
            words = sub_args.split()

            for i, w in enumerate(words):
                if skip_next:
                    skip_next = False
                    continue
                if w.lower() in ("--priority", "-p") and i + 1 < len(words):
                    priority = words[i + 1].lower()
                    skip_next = True
                elif w.lower() in ("--due", "-d") and i + 1 < len(words):
                    due_date = words[i + 1]
                    skip_next = True
                else:
                    title_parts.append(w)

            task_title = " ".join(title_parts).strip()
            if not task_title:
                return "Error: Task title cannot be empty."

            try:
                task = self.task_db.add_task(task_title, priority=priority, due_date=due_date)
                due_info = f" (due: {task.due_date})" if task.due_date else ""
                return f"Task #{task.id} created: '{task.title}' [{task.priority.upper()}]{due_info}"
            except ValueError as err:
                return f"Error creating task: {err}"

        # task done <id> / complete <id>
        if sub_cmd in ("done", "complete", "check"):
            if not sub_args:
                return "Usage: task done <id> (e.g. 'task done 1')"
            try:
                task_id = int(sub_args.lstrip("#"))
            except ValueError:
                return f"Invalid task ID: '{sub_args}'. Must be a number."

            if self.task_db.complete_task(task_id):
                return f"Task #{task_id} marked as completed!"
            return f"Task #{task_id} not found or was already completed."

        # task delete <id> / rm <id>
        if sub_cmd in ("delete", "rm", "remove"):
            if not sub_args:
                return "Usage: task delete <id> (e.g. 'task delete 1')"
            try:
                task_id = int(sub_args.lstrip("#"))
            except ValueError:
                return f"Invalid task ID: '{sub_args}'. Must be a number."

            if self.task_db.delete_task(task_id):
                return f"Task #{task_id} deleted."
            return f"Task #{task_id} not found."

        # task clear (remove completed tasks)
        if sub_cmd in ("clear", "cleanup"):
            cleared = self.task_db.clear_completed_tasks()
            return f"Cleared {cleared} completed task(s)."

        # Default fallback for unrecognized task subcommand
        return (
            f"Unrecognized task action: '{sub_cmd}'.\n"
            "Supported actions: task add, task list, task done, task delete, task clear"
        )

    def _handle_reminder_command(self, cmd_key: str, args: str) -> str:
        """Process 'remind' and 'reminders' subcommands."""
        if not self.task_db:
            return "Reminder database is not initialized."

        trimmed = args.strip()

        # 'reminders' or 'reminder list'
        if cmd_key == "reminders" or (cmd_key == "reminder" and (not trimmed or trimmed.lower().startswith("list"))):
            reminders = self.task_db.list_reminders()
            return format_reminders_list(reminders)

        # 'reminder cancel <id>' or 'reminder delete <id>'
        if trimmed.lower().startswith(("cancel ", "rm ", "delete ")):
            id_str = trimmed.split(maxsplit=1)[1].strip().lstrip("#")
            try:
                rem_id = int(id_str)
            except ValueError:
                return f"Invalid reminder ID: '{id_str}'. Must be a number."

            if self.task_db.cancel_reminder(rem_id):
                return f"Reminder #{rem_id} has been cancelled."
            return f"Reminder #{rem_id} not found or not in scheduled state."

        # 'remind <when> to <message>'
        dt, msg, err = parse_reminder_command(trimmed)
        if err:
            return err
        if not dt or not msg:
            return "Unable to parse reminder time and message. Example: 'remind in 15m to take a break'"

        try:
            reminder = self.task_db.add_reminder(msg, dt.isoformat())
            time_display = dt.strftime("%Y-%m-%d %H:%M UTC")
            return f"Reminder #{reminder.id} scheduled for {time_display}: '{reminder.message}'"
        except ValueError as exc:
            return f"Error scheduling reminder: {exc}"

    def _is_conversational(self, text: str) -> bool:
        """Detect conversational questions or natural language queries."""
        lowered = text.lower()
        conversational_patterns = [
            r"^(hi|hello|hey|howdy|greetings)\b",
            r"^(who|what|why|where|when|how|can you|could you|tell me|explain|write|generate)\b",
            r"^(are you|do you have|what's your name|who made you)\b",
        ]
        return any(re.search(pat, lowered) for pat in conversational_patterns)
