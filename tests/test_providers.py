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
from aura.providers.nvidia import NvidiaProvider
from aura.router import CommandRouter


# ---------------------------------------------------------------------------
# GeminiProvider tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# NvidiaProvider tests
# ---------------------------------------------------------------------------

def test_nvidia_provider_availability():
    # Without key
    prov_no_key = NvidiaProvider(api_key=None)
    assert not prov_no_key.is_available()
    assert prov_no_key.get_provider_name() == "NVIDIA NIM"
    assert "nemotron" in prov_no_key.get_model_name()

    # With key
    prov_with_key = NvidiaProvider(api_key="nvapi-testkey", model_name="nvidia/llama-3.1-nemotron-nano-8b-v1")
    assert prov_with_key.is_available()
    assert prov_with_key.get_model_name() == "nvidia/llama-3.1-nemotron-nano-8b-v1"


def test_nvidia_missing_key_guidance():
    prov = NvidiaProvider(api_key="")
    resp = prov.generate_response("Hello")
    assert "NVIDIA_API_KEY is not set" in resp
    assert "https://build.nvidia.com" in resp


def test_nvidia_empty_prompt():
    prov = NvidiaProvider(api_key="nvapi-fake")
    resp = prov.generate_response("   ")
    assert "Please provide a query" in resp


def test_nvidia_successful_mock_response():
    mock_api_reply = {
        "choices": [
            {
                "message": {
                    "content": "The speed of light is approximately 299,792 km/s."
                }
            }
        ]
    }
    mock_bytes = json.dumps(mock_api_reply).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_bytes
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        prov = NvidiaProvider(api_key="nvapi-valid")
        answer = prov.generate_response("What is the speed of light?")
        assert "299,792" in answer


def test_nvidia_http_401_auth_error():
    mock_err = urllib.error.HTTPError(
        url="https://integrate.api.nvidia.com/v1/chat/completions",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b"{}"),
    )
    with patch("urllib.request.urlopen", side_effect=mock_err):
        prov = NvidiaProvider(api_key="nvapi-bad")
        answer = prov.generate_response("Hello")
        assert "Authentication Error" in answer
        assert "HTTP 401" in answer


def test_nvidia_http_404_model_not_accessible():
    mock_err = urllib.error.HTTPError(
        url="https://integrate.api.nvidia.com/v1/chat/completions",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=io.BytesIO(b"{}"),
    )
    with patch("urllib.request.urlopen", side_effect=mock_err):
        prov = NvidiaProvider(api_key="nvapi-valid")
        answer = prov.generate_response("Hello")
        assert "HTTP 404" in answer
        assert "not accessible" in answer


def test_nvidia_http_410_model_eol():
    mock_err = urllib.error.HTTPError(
        url="https://integrate.api.nvidia.com/v1/chat/completions",
        code=410,
        msg="Gone",
        hdrs={},
        fp=io.BytesIO(b"{}"),
    )
    with patch("urllib.request.urlopen", side_effect=mock_err):
        prov = NvidiaProvider(api_key="nvapi-valid")
        answer = prov.generate_response("Hello")
        assert "HTTP 410" in answer
        assert "end-of-life" in answer


def test_nvidia_network_error():
    mock_err = urllib.error.URLError(reason="No internet")
    with patch("urllib.request.urlopen", side_effect=mock_err):
        prov = NvidiaProvider(api_key="nvapi-valid")
        answer = prov.generate_response("Hello")
        assert "Network Error" in answer
        assert "calc, files, read remain fully functional" in answer


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------

def test_factory_creates_nvidia_provider(tmp_path: Path):
    cfg = AuraConfig(
        app_name="AURA",
        version="0.1.0",
        workspace_dir=tmp_path,
        log_level="INFO",
        ai_provider="nvidia",
        nvidia_api_key="nvapi-testkey123",
        ai_model="nvidia/llama-3.1-nemotron-nano-8b-v1",
    )
    prov = create_llm_provider(cfg)
    assert isinstance(prov, NvidiaProvider)
    assert prov.is_available()


def test_factory_creates_gemini_provider(tmp_path: Path):
    cfg = AuraConfig(
        app_name="AURA",
        version="0.1.0",
        workspace_dir=tmp_path,
        log_level="INFO",
        ai_provider="gemini",
        gemini_api_key="AIzaSy-testkey",
        ai_model="gemini-1.5-flash",
    )
    prov = create_llm_provider(cfg)
    assert isinstance(prov, GeminiProvider)
    assert prov.is_available()


def test_factory_nvidia_no_key(tmp_path: Path):
    cfg = AuraConfig(
        app_name="AURA",
        version="0.1.0",
        workspace_dir=tmp_path,
        log_level="INFO",
        ai_provider="nvidia",
        nvidia_api_key=None,
    )
    prov = create_llm_provider(cfg)
    assert isinstance(prov, NvidiaProvider)
    assert not prov.is_available()


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
