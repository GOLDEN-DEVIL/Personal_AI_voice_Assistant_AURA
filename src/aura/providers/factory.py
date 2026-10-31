"""Provider factory for creating LLM instances from configuration."""

from __future__ import annotations

import logging
from typing import Optional

from aura.config import AuraConfig
from aura.providers.base import BaseLLMProvider
from aura.providers.gemini import GeminiProvider
from aura.providers.nvidia import NvidiaProvider

logger = logging.getLogger(__name__)


def create_llm_provider(config: AuraConfig) -> Optional[BaseLLMProvider]:
    """Create and return configured LLM provider instance.

    Returns:
        Configured BaseLLMProvider or None if disabled.
    """
    provider_name = config.ai_provider.lower().strip()

    if provider_name in ("nvidia", "nim"):
        return NvidiaProvider(
            api_key=config.nvidia_api_key,
            model_name=config.ai_model,
            system_prompt=config.ai_system_prompt,
        )

    if provider_name in ("gemini", "google"):
        return GeminiProvider(
            api_key=config.gemini_api_key,
            model_name=config.ai_model,
            system_prompt=config.ai_system_prompt,
        )

    logger.warning("Unrecognized AI provider '%s'. Defaulting to NVIDIA NIM.", provider_name)
    return NvidiaProvider(
        api_key=config.nvidia_api_key,
        model_name=config.ai_model,
        system_prompt=config.ai_system_prompt,
    )
