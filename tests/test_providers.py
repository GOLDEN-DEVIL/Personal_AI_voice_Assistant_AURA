"""Unit tests for Stage 4 AI providers and LLM integration."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aura.config import AuraConfig
from aura.providers.base import BaseLLMProvider
from aura.providers.factory import create_llm_provider
from aura.providers.gemini import GeminiProvider
from aura.router import CommandRouter


def test_gemini_provider_availability():
    # Without key
    prov_no_key = GeminiProvider(api_key=None)
    assert not prov_no_key.is_available()
    assert prov_no_key.get_provider_name() == "Google Gemini"
    assert prov_no_key.get_model_name() == "gemini-1.5-flash"

    # With key
    prov_with_key = GeminiProvider(api_key="test_key_123", model_name="gemini-2.0-flash")
    assert prov_with_key.is_available()
    assert prov_with_key.get_model_name() == "gemini-2.0-flash"


def test_gemini_missing_key_guidance():
    prov = GeminiProvider(api_key="")
    resp = prov.generate_response("Hello, what is AI?")
    assert "GEMINI_API_KEY is not set" in resp
    assert "https://aistudio.google.com/app/apikey" in resp


def test_gemini_empty_prompt():
    prov = GeminiProvider(api_key="fake_key")
    resp = prov.generate_response("   ")
    assert "Please provide a query" in resp


def test_gemini_successful_mock_response():
    mock_api_reply = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Python is a high-level programming language."}
                    ]
                }
            }
        ]
    }
    mock_bytes = json.dumps(mock_api_reply).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_bytes
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        prov = GeminiProvider(api_key="valid_test_key")
        answer = prov.generate_response("What is Python?")
        assert answer == "Python is a high-level programming language."


def test_gemini_http_403_auth_error():
    mock_err = urllib.error.HTTPError(
        url="https://api.test",
        code=403,
        msg="Forbidden",
        hdrs={},
        fp=io.BytesIO(b"{}"),
    )

    with patch("urllib.request.urlopen", side_effect=mock_err):
        prov = GeminiProvider(api_key="bad_key")
        answer = prov.generate_response("Hello")
        assert "Authentication Error" in answer
        assert "HTTP 403" in answer


def test_gemini_http_429_rate_limit():
    mock_err = urllib.error.HTTPError(
        url="https://api.test",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=io.BytesIO(b"{}"),
    )

    with patch("urllib.request.urlopen", side_effect=mock_err):
        prov = GeminiProvider(api_key="test_key")
        answer = prov.generate_response("Hello")
        assert "Rate Limit" in answer
        assert "HTTP 429" in answer


def test_gemini_network_connection_error():
    mock_err = urllib.error.URLError(reason="No internet connection")

    with patch("urllib.request.urlopen", side_effect=mock_err):
        prov = GeminiProvider(api_key="test_key")
        answer = prov.generate_response("Hello")
        assert "Network Error" in answer
        assert "calc, files, read remain fully functional" in answer


def test_factory_creation(tmp_path: Path):
    cfg_no_key = AuraConfig(
        app_name="AURA",
        version="0.1.0",
        workspace_dir=tmp_path,
        log_level="INFO",
        ai_provider="gemini",
        gemini_api_key=None,
    )
    prov = create_llm_provider(cfg_no_key)
    assert isinstance(prov, GeminiProvider)
    assert not prov.is_available()

    cfg_with_key = AuraConfig(
        app_name="AURA",
        version="0.1.0",
        workspace_dir=tmp_path,
        log_level="INFO",
        ai_provider="gemini",
        gemini_api_key="secret_key_123",
        ai_model="gemini-1.5-flash",
    )
    prov_with_key = create_llm_provider(cfg_with_key)
    assert isinstance(prov_with_key, GeminiProvider)
    assert prov_with_key.is_available()


def test_router_integration_with_mock_llm(tmp_path: Path):
    cfg = AuraConfig(
        app_name="AURA",
        version="0.1.0",
        workspace_dir=tmp_path,
        log_level="INFO",
    )

    mock_llm = MagicMock(spec=BaseLLMProvider)
    mock_llm.is_available.return_value = True
    mock_llm.generate_response.return_value = "Photosynthesis is the process by which plants convert sunlight to energy."

    router = CommandRouter(cfg, llm_provider=mock_llm)

    # 1. Explicit 'ask' command
    reply, should_exit = router.execute("ask how plants make food")
    assert "Photosynthesis" in reply
    assert not should_exit

    # 2. Conversational query without 'ask' prefix
    reply_conv, _ = router.execute("what is photosynthesis?")
    assert "Photosynthesis" in reply_conv

    # 3. Local tool command still executes locally (does NOT call LLM)
    reply_calc, _ = router.execute("calc 25 * 4")
    assert "Result: 100" in reply_calc
