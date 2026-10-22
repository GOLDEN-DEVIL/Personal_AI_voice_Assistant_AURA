"""Text-to-Speech (TTS) engine using pyttsx3."""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("aura.audio.tts")


class TextToSpeechEngine:
    """Offline Text-to-Speech engine wrapper with safety controls and text filtering."""

    def __init__(
        self,
        enabled: bool = False,
        rate: int = 180,
        volume: float = 0.9,
    ) -> None:
        self.enabled = enabled
        self.rate = rate
        self.volume = max(0.0, min(1.0, volume))
        self.available = False
        self._engine: Optional[object] = None

        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize pyttsx3 engine safely."""
        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
            self.available = True
            logger.info("TTS engine initialized successfully.")
        except ImportError:
            logger.warning("pyttsx3 is not installed. TTS voice output is disabled.")
            self.available = False
        except Exception as err:
            logger.warning("Could not initialize audio speaker driver: %s", err)
            self.available = False

    def clean_text_for_speech(self, text: str) -> str:
        """Filter out terminal ASCII tables, dividers, and long code blocks before speaking.

        Prevents reading table borders ('===', '---') and raw column lists aloud.
        """
        lines = text.strip().splitlines()
        speech_lines = []

        for line in lines:
            trimmed = line.strip()
            # Skip separator lines
            if re.match(r"^[\=\-\_\*\#\+]{3,}$", trimmed):
                continue
            # Skip lines that look like table column separators or empty rows
            if trimmed.startswith(("|", "+-", "-+")):
                continue
            # Strip inline decorative markers like === or ---
            cleaned_line = re.sub(r"[\=\-\_\*\#]{3,}", "", trimmed).strip()
            if cleaned_line:
                speech_lines.append(cleaned_line)

        clean = " ".join(speech_lines)
        # Limit spoken text to ~350 characters to avoid endless recitation
        if len(clean) > 350:
            clean = clean[:350].rsplit(" ", 1)[0] + "... and more."

        return clean

    def speak(self, text: str) -> bool:
        """Speak the given text if TTS is enabled and available."""
        if not self.enabled:
            return False

        if not self.available or self._engine is None:
            logger.debug("TTS speak requested but engine is unavailable.")
            return False

        clean_text = self.clean_text_for_speech(text)
        if not clean_text:
            return False

        try:
            self._engine.say(clean_text)
            self._engine.runAndWait()
            return True
        except Exception as err:
            logger.warning("TTS speech synthesis error: %s", err)
            return False

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable voice output."""
        self.enabled = enabled

    def set_rate(self, rate: int) -> None:
        """Set speaking rate in words per minute."""
        self.rate = rate
        if self._engine:
            try:
                self._engine.setProperty("rate", self.rate)
            except Exception:
                pass

    def set_volume(self, volume: float) -> None:
        """Set voice volume between 0.0 and 1.0."""
        self.volume = max(0.0, min(1.0, volume))
        if self._engine:
            try:
                self._engine.setProperty("volume", self.volume)
            except Exception:
                pass
