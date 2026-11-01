"""Zero-API-key web search provider using DuckDuckGo and standard library urllib."""

from __future__ import annotations

import logging
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import List

from aura.search.base import BaseSearchProvider, SearchResult
from aura.search.safety import sanitize_search_result

logger = logging.getLogger(__name__)

# Standard user-agent to ensure normal HTTP compatibility
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class _DDGHTMLParser(HTMLParser):
    """HTML parser to extract titles, URLs, and snippets from DuckDuckGo HTML output."""

    def __init__(self) -> None:
        super().__init__()
        self.results: List[dict[str, str]] = []
        self._current_result: dict[str, str] = {}
        self._capture_title = False
        self._capture_snippet = False
        self._title_buffer: list[str] = []
        self._snippet_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k: v or "" for k, v in attrs}
        css_class = attr_dict.get("class", "")

        # Result link: <a class="result__a" href="...">
        if tag == "a" and "result__a" in css_class:
            href = attr_dict.get("href", "")
            # DuckDuckGo wraps URLs in '/l/?uddg=<actual_url>&...' or direct href
            actual_url = self._extract_actual_url(href)
            self._current_result = {"url": actual_url, "title": "", "snippet": ""}
            self._capture_title = True
            self._title_buffer = []

        # Result snippet: <a class="result__snippet" ...> or <div class="result__snippet">
        elif "result__snippet" in css_class:
            self._capture_snippet = True
            self._snippet_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture_title:
            self._capture_title = False
            if self._current_result:
                self._current_result["title"] = "".join(self._title_buffer).strip()

        if self._capture_snippet:
            self._capture_snippet = False
            if self._current_result:
                self._current_result["snippet"] = "".join(self._snippet_buffer).strip()
                if self._current_result.get("url") and self._current_result.get("title"):
                    self.results.append(self._current_result)
                self._current_result = {}

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._title_buffer.append(data)
        elif self._capture_snippet:
            self._snippet_buffer.append(data)

    @staticmethod
    def _extract_actual_url(href: str) -> str:
        """Extract destination URL from DuckDuckGo redirect link."""
        if "uddg=" in href:
            parsed = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed.query)
            if "uddg" in params and params["uddg"]:
                return params["uddg"][0]
        return href


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """Web search provider powered by DuckDuckGo (requires zero API keys)."""

    def __init__(self, timeout: int = 8) -> None:
        self.timeout = timeout
        self.endpoint = "https://html.duckduckgo.com/html/"

    def is_available(self) -> bool:
        """DuckDuckGo requires no credentials and is always available."""
        return True

    def get_provider_name(self) -> str:
        return "DuckDuckGo (Zero-Key)"

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Perform search query against DuckDuckGo HTML endpoint."""
        trimmed = query.strip()
        if not trimmed:
            return []

        data = urllib.parse.urlencode({"q": trimmed}).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html_content = resp.read().decode("utf-8", errors="replace")

            parser = _DDGHTMLParser()
            parser.feed(html_content)

            sanitized_results: list[SearchResult] = []
            for item in parser.results:
                raw_result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                )
                safe = sanitize_search_result(raw_result)
                if safe:
                    sanitized_results.append(safe)
                if len(sanitized_results) >= max_results:
                    break

            return sanitized_results

        except Exception as exc:
            logger.warning("DuckDuckGo search error: %s", exc)
            return []

