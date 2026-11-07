"""Unit and security tests for Wake-Word detection, state transitions, and privacy controls."""

from __future__ import annotations

import pytest

from aura.audio.wakeword import WakeWordDetector, WakeWordState
from aura.config import AuraConfig
from aura.router import CommandRouter


# ---------------------------------------------------------------------------
# 1. Privacy & Opt-In Defaults Tests
# ---------------------------------------------------------------------------

def test_wakeword_disabled_by_default():
    """Wake-word detection MUST be disabled by default (explicit opt-in requirement)."""
    detector = WakeWordDetector()
    assert detector.is_enabled() is False
    assert detector.state == WakeWordState.DISABLED
    assert detector.enabled is False


def test_wakeword_enable_and_disable():
    """Enabling transitions to IDLE; disabling transitions to DISABLED."""
    detector = WakeWordDetector()

    detector.set_enabled(True)
    assert detector.is_enabled() is True
    assert detector.state == WakeWordState.IDLE

    detector.set_enabled(False)
    assert detector.is_enabled() is False
    assert detector.state == WakeWordState.DISABLED


def test_wakeword_pause_and_resume():
    """Pausing suppresses listening (preventing self-trigger during TTS); resume restores state."""
    detector = WakeWordDetector(enabled=True)
    assert detector.state == WakeWordState.IDLE

    detector.pause()
    assert detector.state == WakeWordState.PAUSED
    # Cannot listen while paused
    assert detector.listen_for_wake_word() is False

    detector.resume()
    assert detector.state == WakeWordState.IDLE


def test_wakeword_state_change_callback():
    """State change callback must be notified upon every transition."""
    history = []
    detector = WakeWordDetector(on_state_change=lambda s: history.append(s))

    detector.set_enabled(True)
    detector.pause()
    detector.resume()
    detector.set_enabled(False)

    assert WakeWordState.IDLE in history
    assert WakeWordState.PAUSED in history
    assert WakeWordState.DISABLED in history


# ---------------------------------------------------------------------------
# 2. Text Phrase Matching Tests
# ---------------------------------------------------------------------------

def test_check_text_for_wakeword_matches():
    """check_text_for_wakeword should match configured target phrase variations."""
    detector = WakeWordDetector(wake_word="hey aura")

    assert detector.check_text_for_wakeword("hey aura") is True
    assert detector.check_text_for_wakeword("Hey Aura, what time is it?") is True
    assert detector.check_text_for_wakeword("Aura calculate 25 * 4") is True
    assert detector.check_text_for_wakeword("ok aura tell me a joke") is True
    assert detector.check_text_for_wakeword("hi aura") is True


def test_check_text_for_wakeword_rejects():
    """Non-matching phrases should never trigger the wake word."""
    detector = WakeWordDetector(wake_word="hey aura")

    assert detector.check_text_for_wakeword("hello world") is False
    assert detector.check_text_for_wakeword("hey siri") is False
    assert detector.check_text_for_wakeword("alexa turn on lights") is False
    assert detector.check_text_for_wakeword("") is False


# ---------------------------------------------------------------------------
# 3. Status and Diagnostics Tests
# ---------------------------------------------------------------------------

def test_wakeword_status_metadata():
    """get_status should return complete diagnostic information."""
    detector = WakeWordDetector(wake_word="hey aura", threshold=0.7, enabled=True)
    st = detector.get_status()

    assert st["enabled"] is True
    assert st["wake_word"] == "hey aura"
    assert st["threshold"] == 0.7
    assert "engine" in st
    assert "available" in st
    assert st["state"] == "idle"


# ---------------------------------------------------------------------------
# 4. CommandRouter Wake-Word Integration Tests
# ---------------------------------------------------------------------------

def test_router_wakeword_status(tmp_path):
    """Router 'wakeword status' command reports current detector state."""
    cfg = AuraConfig(app_name="AURA", version="0.1.0", workspace_dir=tmp_path, log_level="INFO")
    detector = WakeWordDetector(enabled=False)
    router = CommandRouter(cfg, wakeword_detector=detector)

    resp, exit_flag = router.execute("wakeword status")
    assert exit_flag is False
    assert "Wake-Word Detection is currently DISABLED" in resp
    assert "Trigger Phrase : \"hey aura\"" in resp


def test_router_wakeword_toggle(tmp_path):
    """Router 'wakeword on' and 'wakeword off' commands toggle detector state."""
    cfg = AuraConfig(app_name="AURA", version="0.1.0", workspace_dir=tmp_path, log_level="INFO")
    detector = WakeWordDetector(enabled=False)
    router = CommandRouter(cfg, wakeword_detector=detector)

    resp_on, _ = router.execute("wakeword on")
    assert "Wake-word detection ('hey aura') is now ENABLED." in resp_on
    assert detector.is_enabled() is True

    resp_off, _ = router.execute("wakeword off")
    assert "Wake-word detection is now DISABLED." in resp_off
    assert detector.is_enabled() is False


def test_router_wakeword_uninitialized(tmp_path):
    """Router without detector instance handles commands gracefully."""
    cfg = AuraConfig(app_name="AURA", version="0.1.0", workspace_dir=tmp_path, log_level="INFO")
    router = CommandRouter(cfg, wakeword_detector=None)

    resp, _ = router.execute("wakeword on")
    assert "Wake-word detector is not initialized" in resp

