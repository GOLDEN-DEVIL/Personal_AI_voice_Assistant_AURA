"""Abstract base classes and data models for web search providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SearchResult:
    """Represents a single verified web search result.

    Attributes:
        title: Title of the webpage or resource.
        url: Direct HTTP/HTTPS URL of the source.
        snippet: Concise textual summary or extract from the page.
        raw_content: Optional extended text content if available.
    """

    title: str
    url: str
    snippet: str
    raw_content: Optional[str] = None


class BaseSearchProvider(ABC):
    """Abstract interface for all web search engine providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available (e.g., credentials or network)."""
        pass

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Perform a web search for the given query.

        Args:
            query: User search query terms.
            max_results: Maximum number of search results to return (default 5).

        Returns:
            A list of sanitized SearchResult objects.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name (e.g. 'DuckDuckGo', 'Tavily')."""
        pass

