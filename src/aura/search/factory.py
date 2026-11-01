"""Search provider factory for creating web search instances from configuration."""

from __future__ import annotations

import logging
from typing import Optional

from aura.config import AuraConfig
from aura.search.base import BaseSearchProvider
from aura.search.duckduckgo import DuckDuckGoSearchProvider
from aura.search.tavily import TavilySearchProvider

logger = logging.getLogger(__name__)


def create_search_provider(config: AuraConfig) -> BaseSearchProvider:
    """Create and return configured web search provider instance.

    Args:
        config: Application configuration.

    Returns:
        Configured BaseSearchProvider. Defaults to DuckDuckGo if unconfigured or unrecognized.
    """
    provider_name = getattr(config, "search_provider", "duckduckgo").lower().strip()

    if provider_name in ("tavily", "tavilyai"):
        tavily_key = getattr(config, "tavily_api_key", None)
        if tavily_key:
            return TavilySearchProvider(api_key=tavily_key)
        logger.warning("Tavily provider requested but TAVILY_API_KEY is not set. Falling back to DuckDuckGo.")
        return DuckDuckGoSearchProvider()

    if provider_name in ("duckduckgo", "ddg"):
        return DuckDuckGoSearchProvider()

    logger.warning("Unrecognized search provider '%s'. Defaulting to DuckDuckGo.", provider_name)
    return DuckDuckGoSearchProvider()

