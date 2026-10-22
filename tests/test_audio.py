"""Unit tests for Stage 3 audio components (TTS and STT)."""

from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from aura.audio.stt import SpeechToTextListener
from aura.audio.tts import TextToSpeechEngine
from aura.config import AuraConfig
from aura.router import CommandRouter


def test_tts_initialization():
    tts = TextToSpeechEngine(enabled=False, rate=160, volume=0.8)
    assert not tts.enabled
    assert tts.rate == 160
    assert tts.volume == 0.8


def test_tts_clean_text_for_speech():
    tts = TextToSpeechEngine(enabled=False)

    raw_output = """
======================================================
=== File: notes.txt (42 characters) ===
------------------------------------------------------
Meeting notes content here.
======================================================
"""
    clean = tts.clean_text_for_speech(raw_output)
    assert "===" not in clean
    assert "---" not in clean
    assert "===" not in clean
    assert "Meeting notes content here." in clean


def test_tts_clean_text_length_limit():
    tts = TextToSpeechEngine(enabled=False)
    giant_text = "word " * 200
    cleaned = tts.clean_text_for_speech(giant_text)
    assert len(cleaned) <= 365
    assert "... and more." in cleaned


def test_tts_toggle_and_properties():
    tts = TextToSpeechEngine(enabled=False)
    tts.set_enabled(True)
    assert tts.enabled

    tts.set_rate(200)
    assert tts.rate == 200

    tts.set_volume(0.5)
    assert tts.volume == 0.5


def test_tts_speak_when_disabled():
    tts = TextToSpeechEngine(enabled=False)
    # Should safely return False without attempting audio playback
    assert tts.speak("Hello there") is False


def test_stt_initialization():
    stt = SpeechToTextListener(timeout=3, phrase_time_limit=5)
    assert stt.timeout == 3
    assert stt.phrase_time_limit == 5


def test_stt_transcription_with_mock():
    stt = SpeechToTextListener()
    if not stt.available:
        pytest.skip("SpeechRecognition not available")

    with patch.object(stt, "_recognizer") as mock_rec, \
         patch.object(stt._sr_module, "Microphone") as mock_mic:
        mock_rec.recognize_google.return_value = "hello aura"
        text, err = stt.listen_and_transcribe()
        assert text == "hello aura"
        assert err is None


def test_stt_timeout_with_mock():
    stt = SpeechToTextListener()
    if not stt.available:
        pytest.skip("SpeechRecognition not available")

    with patch.object(stt, "_recognizer") as mock_rec, \
         patch.object(stt._sr_module, "Microphone"):
        mock_rec.listen.side_effect = stt._sr_module.WaitTimeoutError("Timeout")
        text, err = stt.listen_and_transcribe()
        assert text is None
        assert "timed out" in err.lower()


def test_router_voice_commands(tmp_path: Path):
    cfg = AuraConfig(
        app_name="AURA_TEST",
        version="0.1.0-test",
        workspace_dir=tmp_path,
        log_level="DEBUG",
    )
    tts = TextToSpeechEngine(enabled=False)
    router = CommandRouter(cfg, tts_engine=tts)

    # Test status
    res_status, _ = router.execute("voice status")
    assert "DISABLED" in res_status

    # Test enable
    res_on, _ = router.execute("voice on")
    assert "ENABLED" in res_on
    assert tts.enabled is True

    # Test disable
    res_off, _ = router.execute("voice off")
    assert "DISABLED" in res_off
    assert tts.enabled is False

    # Test alias tts on
    res_tts_on, _ = router.execute("tts on")
    assert "ENABLED" in res_tts_on
    assert tts.enabled is True

    # Test listen trigger
    res_listen, _ = router.execute("listen")
    assert "Push-to-talk" in res_listen
