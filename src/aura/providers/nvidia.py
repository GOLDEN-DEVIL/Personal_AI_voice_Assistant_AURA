"""NVIDIA NIM LLM provider implementation via OpenAI-compatible REST API."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from aura.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are AURA (AI Utility & Response Assistant), a polite, concise, and helpful personal voice assistant. "
    "Provide clear, direct, and conversational responses. Avoid overly long replies or unnecessary markup "
    "so that answers sound natural when read aloud."
)

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"


class NvidiaProvider(BaseLLMProvider):
    """NVIDIA NIM AI provider using OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "nvidia/nemotron-3.5-bolt-e4b",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.model_name = model_name or "nvidia/nemotron-3.5-bolt-e4b"
        self.system_prompt = system_prompt
        self.timeout = timeout_seconds

    def is_available(self) -> bool:
        """Return True if an NVIDIA API key is configured."""
        return bool(self.api_key)

    def get_provider_name(self) -> str:
        return "NVIDIA NIM"

    def get_model_name(self) -> str:
        return self.model_name

    def generate_response(self, prompt: str) -> str:
        """Generate a response from an NVIDIA NIM hosted model."""
        if not self.is_available():
            return (
                "AI Error: NVIDIA_API_KEY is not set.\n"
                "To enable conversational AI, add your key to .env:\n"
                "  NVIDIA_API_KEY=nvapi-...\n"
                "Get a free API key at https://build.nvidia.com"
            )

        trimmed = prompt.strip()
        if not trimmed:
            return "Please provide a query or question for the AI."

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": trimmed},
            ],
            "temperature": 0.7,
            "max_tokens": 600,
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{NVIDIA_API_BASE}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data_json = json.loads(resp.read().decode("utf-8"))
                choices = data_json.get("choices", [])
                if not choices:
                    return "AI Notice: The model did not return a response."
                text = choices[0].get("message", {}).get("content", "").strip()
                return text or "AI Notice: Empty text response received."

        except urllib.error.HTTPError as err:
            logger.error("NVIDIA NIM API HTTP error %d: %s", err.code, err.reason)
            detail = ""
            try:
                raw_body = err.read().decode("utf-8")
                err_json = json.loads(raw_body)
                detail = (
                    err_json.get("detail", "")
                    or err_json.get("message", "")
                    or err_json.get("error", {}).get("message", "")
                )
            except Exception:
                detail = ""

            if err.code == 401:
                return (
                    "AI Authentication Error (HTTP 401): The NVIDIA_API_KEY is invalid or expired.\n"
                    "Please verify your key starts with 'nvapi-' and is correctly set in .env.\n"
                    "Get a key at https://build.nvidia.com"
                )
            if err.code == 402:
                return (
                    "AI Error (HTTP 402): NVIDIA NIM credits exhausted or billing required.\n"
                    "Please check your account at https://build.nvidia.com"
                )
            if err.code == 404:
                return (
                    f"AI Error (HTTP 404): Model '{self.model_name}' is not accessible on your account tier.\n"
                    "Try a different model by setting AURA_AI_MODEL in .env.\n"
                    "Browse available models at https://build.nvidia.com/explore/discover"
                )
            if err.code == 410:
                return (
                    f"AI Error (HTTP 410): Model '{self.model_name}' has reached end-of-life and is no longer available.\n"
                    "Please update AURA_AI_MODEL in .env to an active model.\n"
                    "Browse available models at https://build.nvidia.com/explore/discover"
                )
            if err.code == 429:
                return (
                    "AI Rate Limit (HTTP 429): NVIDIA NIM request limit exceeded.\n"
                    "Please wait a moment before asking another question."
                )
            detail_msg = f" ({detail})" if detail else f": {err.reason}"
            return f"AI Service Error (HTTP {err.code}){detail_msg}. Please try again later."

        except urllib.error.URLError as err:
            logger.warning("Network connection failed during NVIDIA NIM API call: %s", err.reason)
            return (
                "AI Network Error: Could not connect to NVIDIA NIM servers.\n"
                "Please verify your internet connection. (Local commands like calc, files, read remain fully functional)."
            )

        except TimeoutError:
            logger.warning("NVIDIA NIM API call timed out after %d seconds.", self.timeout)
            return "AI Error: The request to NVIDIA NIM timed out. Please try again."

        except Exception as err:
            logger.exception("Unexpected error while querying NVIDIA NIM API: %s", err)
            return f"AI Error: An unexpected error occurred: {err}"

