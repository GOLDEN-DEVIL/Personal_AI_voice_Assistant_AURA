"""Text formatting utilities for memory displays and LLM prompt context injection."""

from __future__ import annotations

import re
from typing import Optional

from aura.memory.models import DialogueTurn, MemoryItem
from aura.memory.store import MemoryStore
from aura.memory.context import ConversationContext

MAX_PROMPT_MEMORY_CHARS = 1500


def sanitize_for_prompt(text: str) -> str:
    """Sanitize user text to prevent prompt injection when injected into LLM context."""
    if not text:
        return ""
    # Neutralize markdown system override phrases
    cleaned = re.sub(
        r"(?i)\b(ignore previous instructions|system prompt|disregard all|you are now|override instructions)\b",
        "[filtered-instruction]",
        text,
    )
    # Strip backticks to prevent prompt breakout
    cleaned = cleaned.replace("```", "'''")
    return cleaned.strip()


def format_memory_list(memories: list[MemoryItem], title: str = "Stored Memories") -> str:
    """Format a list of MemoryItem objects as a structured terminal table."""
    if not memories:
        return (
            "No persistent memories stored.\n"
            "Use 'remember <fact>' or 'memory save <fact>' to remember personal details, preferences, or notes."
        )

    lines = [
        f"=== {title} ({len(memories)} item{'s' if len(memories) != 1 else ''}) ===",
        f"{'ID':<5} | {'Category':<12} | {'Fact / Content'}",
        "-" * 65,
    ]

    for m in memories:
        content_preview = m.content if len(m.content) <= 50 else m.content[:47] + "..."
        lines.append(f"#{m.id:<4} | {m.category:<12} | {content_preview}")

    lines.append("-" * 65)
    lines.append("Commands: memory remember <fact> | memory forget <id> | memory update <id> <text>")
    return "\n".join(lines)


def format_memory_status(
    store: Optional[MemoryStore],
    context: Optional[ConversationContext],
    auto_inject: bool = True,
) -> str:
    """Generate diagnostic status report for the memory subsystem."""
    if not store:
        return "Memory store is not initialized in this session."

    enabled_str = "ENABLED" if store.is_enabled() else "DISABLED (opt-in)"
    fact_count = store.get_count() if store.is_enabled() else 0
    turns_count = context.get_turn_count() if context else 0
    inject_str = "ON" if auto_inject and store.is_enabled() else "OFF"

    return (
        f"Memory Subsystem Status:\n"
        f"  Persistent Memory : [{enabled_str}]\n"
        f"  Stored Facts      : {fact_count} facts (SQLite: {store.db_path.name})\n"
        f"  Session Context   : {turns_count} recent turn(s) in RAM (ephemeral)\n"
        f"  AI Auto-Injection : [{inject_str}]\n"
        f"\n"
        f"Usage Tips:\n"
        f"  'memory on' / 'memory off'        - Toggle persistent memory\n"
        f"  'memory remember <fact>'          - Store a new fact\n"
        f"  'memory list' / 'memory search'   - View stored memories\n"
        f"  'memory forget <id>'              - Delete a memory fact\n"
        f"  'memory session'                  - View short-term conversation context\n"
        f"  'memory session clear'            - Clear short-term context\n"
        f"  'memory inject on|off'            - Toggle AI prompt augmentation"
    )


def format_session_turns(turns: list[DialogueTurn]) -> str:
    """Format short-term conversation history for terminal display."""
    if not turns:
        return "No recent conversation turns in current session memory."

    lines = [
        f"=== Current Session Dialogue Context ({len(turns)} turns) ===",
        "Note: Held in RAM only; automatically wiped upon exit or 'memory session clear'.",
        "-" * 65,
    ]

    for idx, turn in enumerate(turns, 1):
        user_snip = turn.user_query if len(turn.user_query) <= 60 else turn.user_query[:57] + "..."
        resp_snip = turn.assistant_response if len(turn.assistant_response) <= 60 else turn.assistant_response[:57] + "..."
        lines.append(f"Turn #{idx} [{turn.timestamp[11:19]} UTC]:")
        lines.append(f"  User     : {user_snip}")
        lines.append(f"  Assistant: {resp_snip}")

    lines.append("-" * 65)
    return "\n".join(lines)


def format_memory_context_for_llm(
    memories: list[MemoryItem],
    turns: list[DialogueTurn],
) -> str:
    """Format persistent memories and session context into a structured prompt block for LLM.

    Args:
        memories: List of relevant persistent memories.
        turns: Recent dialogue turns from session memory.

    Returns:
        A concise text block for injection into AI system/user context, or empty string.
    """
    blocks: list[str] = []

    if memories:
        fact_lines = []
        for m in memories:
            sanitized_content = sanitize_for_prompt(m.content)
            fact_lines.append(f"- [{m.category}] {sanitized_content}")
        blocks.append("[User Stored Facts & Preferences]:\n" + "\n".join(fact_lines))

    if turns:
        turn_lines = []
        for turn in turns:
            s_user = sanitize_for_prompt(turn.user_query)
            s_resp = sanitize_for_prompt(turn.assistant_response)
            turn_lines.append(f"User: {s_user}\nAssistant: {s_resp}")
        blocks.append("[Recent Conversation History]:\n" + "\n".join(turn_lines))

    if not blocks:
        return ""

    context_str = "\n\n".join(blocks)
    if len(context_str) > MAX_PROMPT_MEMORY_CHARS:
        context_str = context_str[:MAX_PROMPT_MEMORY_CHARS] + "\n[...additional memory truncated]"

    return context_str

