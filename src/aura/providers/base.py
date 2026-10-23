"""Abstract base class for Large Language Model (LLM) providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract interface for conversational AI and LLM providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and has required credentials."""
        pass

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a response from the LLM given a user prompt.

        Args:
            prompt: User conversational text.

        Returns:
            The AI response string or a helpful error message.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the model currently in use."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name (e.g. 'Google Gemini')."""
        pass
