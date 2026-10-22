"""Application orchestrator and interactive command-line loop."""

from __future__ import annotations

import sys
from typing import Optional

from aura.audio.stt import SpeechToTextListener
from aura.audio.tts import TextToSpeechEngine
from aura.config import AuraConfig
from aura.logging_config import setup_logging
from aura.router import CommandRouter


class AuraApp:
    """Core interactive application runtime for Project AURA."""

    def __init__(self, config: Optional[AuraConfig] = None) -> None:
        self.config = config or AuraConfig.load()
        self.logger = setup_logging(self.config.log_level)
        self.tts = TextToSpeechEngine(
            enabled=self.config.tts_enabled,
            rate=self.config.tts_rate,
            volume=self.config.tts_volume,
        )
        self.stt = SpeechToTextListener(
            timeout=self.config.stt_timeout,
            phrase_time_limit=self.config.stt_phrase_limit,
        )
        self.router = CommandRouter(self.config, tts_engine=self.tts)

    def print_banner(self) -> None:
        """Display startup information, workspace, and voice status."""
        tts_state = "ON" if self.tts.enabled else "OFF"
        stt_state = "READY (type 'listen')" if self.stt.available else "UNAVAILABLE"

        banner = f"""
======================================================
  Project AURA - AI Utility & Response Assistant
  Version: {self.config.version} | Mode: Voice & Command
======================================================
  Workspace  : {self.config.workspace_dir}
  Voice TTS  : [{tts_state}] (use 'voice on' / 'voice off')
  Voice PTT  : [{stt_state}]
  Hint       : Type 'help' for commands, 'exit' to quit.
------------------------------------------------------
"""
        print(banner.strip())

    def run(self) -> None:
        """Start the interactive command loop."""
        self.logger.info("Starting AURA interactive session.")
        self.print_banner()

        while True:
            try:
                user_input = input("\nAURA > ")
            except (KeyboardInterrupt, EOFError):
                print("\n\nSession terminated by user. Goodbye!")
                self.logger.info("Session closed via interrupt signal.")
                break

            trimmed = user_input.strip()
            if not trimmed:
                continue

            # Push-to-talk microphone trigger
            if trimmed.lower() in ("listen", "ptt", "mic"):
                transcription, err = self.stt.listen_and_transcribe()
                if err:
                    print(f"\n{err}")
                    if self.tts.enabled:
                        self.tts.speak("Microphone audio capture was unsuccessful.")
                    continue
                if transcription:
                    print(f"\nYou (Voice) > {transcription}")
                    user_input = transcription
                else:
                    continue

            response, should_exit = self.router.execute(user_input)
            print(response)

            # Spoken response if TTS is enabled
            if self.tts.enabled:
                self.tts.speak(response)

            if should_exit:
                self.logger.info("Session closed normally.")
                break


def main() -> int:
    """Entry point for the application."""
    app = AuraApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
