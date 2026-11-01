"""High-precision AI web search provider using the Tavily REST API."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from aura.search.base import BaseSearchProvider, SearchResult
from aura.search.safety import sanitize_search_result

logger = logging.getLogger(__name__)


class TavilySearchProvider(BaseSearchProvider):
    """Web search provider powered by Tavily Search API for AI agents."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.timeout = timeout
        self.endpoint = "https://api.tavily.com/search"

    def is_available(self) -> bool:
        """Check if a valid Tavily API key is configured."""
        return bool(self.api_key and len(self.api_key) > 5)

    def get_provider_name(self) -> str:
        return "Tavily AI Search"

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Perform search query against Tavily REST API."""
        if not self.is_available():
            logger.warning("Tavily search invoked without valid API key.")
            return []

        trimmed = query.strip()
        if not trimmed:
            return []

        payload = {
            "api_key": self.api_key,
            "query": trimmed,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
        }

        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw_bytes = response.read()
                data = json.loads(raw_bytes.decode("utf-8"))

            results_list = data.get("results", [])
            sanitized: list[SearchResult] = []

            for item in results_list:
                raw = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                )
                safe = sanitize_search_result(raw)
                if safe:
                    sanitized.append(safe)
                if len(sanitized) >= max_results:
                    break

            return sanitized

        except urllib.error.HTTPError as http_err:
            logger.error("Tavily API HTTP error: %d %s", http_err.code, http_err.reason)
            return []
        except Exception as exc:
            logger.error("Tavily search network or parsing error: %s", exc)
            return []

