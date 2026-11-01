"""Web search providers and security utilities for Project AURA."""

from aura.search.base import BaseSearchProvider, SearchResult
from aura.search.duckduckgo import DuckDuckGoSearchProvider
from aura.search.factory import create_search_provider
from aura.search.safety import (
    format_search_context_for_llm,
    format_search_results_for_display,
    neutralize_prompt_injection,
    sanitize_search_result,
    sanitize_text,
    validate_url,
)
from aura.search.tavily import TavilySearchProvider

__all__ = [
    "BaseSearchProvider",
    "DuckDuckGoSearchProvider",
    "SearchResult",
    "TavilySearchProvider",
    "create_search_provider",
    "format_search_context_for_llm",
    "format_search_results_for_display",
    "neutralize_prompt_injection",
    "sanitize_search_result",
    "sanitize_text",
    "validate_url",
]
