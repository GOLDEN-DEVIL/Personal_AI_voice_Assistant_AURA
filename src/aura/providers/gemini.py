"""Google Gemini LLM provider implementation via REST API."""

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


class GeminiProvider(BaseLLMProvider):
    """Google Gemini AI provider using standard HTTPS REST calls."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        timeout_seconds: int = 15,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.model_name = model_name or "gemini-1.5-flash"
        self.system_prompt = system_prompt
        self.timeout = timeout_seconds

    def is_available(self) -> bool:
        """Return True if an API key is configured."""
        return bool(self.api_key)

    def get_provider_name(self) -> str:
        return "Google Gemini"

    def get_model_name(self) -> str:
        return self.model_name

    def generate_response(self, prompt: str) -> str:
        """Generate response from Gemini model."""
        if not self.is_available():
            return (
                "AI Error: GEMINI_API_KEY is not set.\n"
                "To enable conversational AI, add your key to .env:\n"
                "  GEMINI_API_KEY=your_gemini_api_key_here\n"
                "Get a free API key at https://aistudio.google.com/app/apikey"
            )

        trimmed = prompt.strip()
        if not trimmed:
            return "Please provide a query or question for the AI."

        url = f"{self.BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": trimmed}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": self.system_prompt}]
            },
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 600,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
                data_json = json.loads(resp_bytes.decode("utf-8"))

                candidates = data_json.get("candidates", [])
                if not candidates:
                    return "AI Notice: The model did not return a response (content may have been filtered)."

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    return "AI Notice: Empty response received from the model."

                text = "".join(part.get("text", "") for part in parts).strip()
                return text or "AI Notice: Empty text response received."

        except urllib.error.HTTPError as err:
            logger.error("Gemini API HTTP error %d: %s", err.code, err.reason)
            if err.code in (400, 403):
                return (
                    f"AI Authentication Error (HTTP {err.code}): The provided GEMINI_API_KEY appears invalid or unauthorized.\n"
                    "Please verify your key in .env or create a new one at https://aistudio.google.com/app/apikey"
                )
            if err.code == 429:
                return (
                    "AI Rate Limit (HTTP 429): Free tier quota or rate limit exceeded.\n"
                    "Please wait a moment before asking another question."
                )
            return f"AI Service Error (HTTP {err.code}): {err.reason}. Please try again later."

        except urllib.error.URLError as err:
            logger.warning("Network connection failed during Gemini API call: %s", err.reason)
            return (
                "AI Network Error: Could not connect to Google Gemini servers.\n"
                "Please verify your internet connection. (Local commands like calc, files, read remain fully functional)."
            )

        except TimeoutError:
            logger.warning("Gemini API call timed out after %d seconds.", self.timeout)
            return "AI Error: The request to Google Gemini timed out. Please try again."

        except Exception as err:
            logger.exception("Unexpected error while querying Gemini API: %s", err)
            return f"AI Error: An unexpected error occurred: {err}"
