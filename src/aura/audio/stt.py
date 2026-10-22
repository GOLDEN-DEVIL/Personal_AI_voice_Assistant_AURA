"""Speech-to-Text (STT) push-to-talk listener using SpeechRecognition."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

logger = logging.getLogger("aura.audio.stt")


class SpeechToTextListener:
    """Push-to-talk microphone listener with privacy controls and graceful fallbacks."""

    def __init__(self, timeout: int = 5, phrase_time_limit: int = 10) -> None:
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.available = False
        self._sr_module = None
        self._recognizer = None

        self._init_recognizer()

    def _init_recognizer(self) -> None:
        """Initialize speech recognition engine safely."""
        try:
            import speech_recognition as sr

            self._sr_module = sr
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self.available = True
            logger.info("Speech recognition module loaded successfully.")
        except ImportError:
            logger.warning("SpeechRecognition is not installed. Voice input is unavailable.")
            self.available = False
        except Exception as err:
            logger.warning("Could not initialize SpeechRecognition: %s", err)
            self.available = False

    def listen_and_transcribe(
        self,
        timeout: Optional[int] = None,
        phrase_time_limit: Optional[int] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Capture microphone audio on push-to-talk and transcribe to text.

        Returns:
            Tuple of (transcribed_text, error_message).
            If successful: (text, None)
            If error: (None, error_message)
        """
        if not self.available or self._sr_module is None or self._recognizer is None:
            return None, (
                "Voice Input Unavailable:\n"
                "The speech recognition library or audio driver is missing.\n"
                "To enable voice input, install dependencies:\n"
                "    pip install SpeechRecognition pyaudio\n"
                "or: pip install .[voice]"
            )

        sr = self._sr_module
        wait_time = timeout or self.timeout
        phrase_limit = phrase_time_limit or self.phrase_time_limit

        try:
            with sr.Microphone() as source:
                print("\n[Adjusting for ambient noise... please wait a moment]")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.8)

                print("[Listening... Speak your command clearly into the microphone]")
                audio = self._recognizer.listen(
                    source,
                    timeout=wait_time,
                    phrase_time_limit=phrase_limit,
                )

                print("[Processing speech...]")
                transcription = self._recognizer.recognize_google(audio)
                clean_text = transcription.strip()
                return clean_text, None

        except sr.WaitTimeoutError:
            return None, "Voice input timed out: No speech detected within the listening window."
        except sr.UnknownValueError:
            return None, "Could not understand audio: Speech was unclear or background noise was too high."
        except sr.RequestError as err:
            return None, f"Speech recognition service error: {err}"
        except OSError as err:
            return None, f"Microphone hardware error: {err} (Is a microphone plugged in and enabled?)"
        except Exception as err:
            return None, f"Voice capture error: {err}"
