"""Application orchestrator and interactive command-line loop."""

from __future__ import annotations

import sys
from typing import Optional

from aura.audio.stt import SpeechToTextListener
from aura.audio.tts import TextToSpeechEngine
from aura.audio.wakeword import WakeWordDetector, WakeWordState
from aura.config import AuraConfig
from aura.logging_config import setup_logging
from aura.providers.factory import create_llm_provider
from aura.router import CommandRouter
from aura.search.factory import create_search_provider
from aura.tasks import Reminder, ReminderScheduler, TaskDatabase


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
        self.wakeword = WakeWordDetector(
            wake_word=self.config.wakeword_model,
            threshold=self.config.wakeword_threshold,
            enabled=self.config.wakeword_enabled,
        )
        self.llm = create_llm_provider(self.config)
        self.search = create_search_provider(self.config)
        db_path = self.config.tasks_db_path or (self.config.workspace_dir / "aura_tasks.db")
        self.task_db = TaskDatabase(db_path)

        def _on_reminder_alert(reminder: Reminder) -> None:
            alert_text = f"\n\n[REMINDER ALERT] {reminder.message}\nAURA > "
            print(alert_text, end="", flush=True)
            if self.tts.enabled:
                self.wakeword.pause()
                try:
                    self.tts.speak(f"Reminder: {reminder.message}")
                finally:
                    self.wakeword.resume()

        self.scheduler = ReminderScheduler(
            self.task_db,
            notification_callback=_on_reminder_alert,
            check_interval_seconds=2.0,
        )
        self.router = CommandRouter(
            self.config,
            tts_engine=self.tts,
            llm_provider=self.llm,
            search_provider=self.search,
            task_db=self.task_db,
            wakeword_detector=self.wakeword,
        )

    def print_banner(self) -> None:
        """Display startup information, workspace, voice, AI, search, and wake-word status."""
        tts_state = "ON" if self.tts.enabled else "OFF"
        stt_state = "READY (type 'listen')" if self.stt.available else "UNAVAILABLE"
        if self.llm and self.llm.is_available():
            ai_state = f"{self.llm.get_provider_name()} ({self.llm.get_model_name()})"
        else:
            ai_state = "LOCAL ONLY (set NVIDIA_API_KEY in .env)"

        search_state = self.search.get_provider_name() if self.search else "DISABLED"

        if self.wakeword and self.wakeword.is_enabled():
            wake_state = f"ACTIVE ('{self.wakeword.wake_word}')"
        else:
            wake_state = "DISABLED (type 'wakeword on')"

        pending_tasks = len(self.task_db.list_tasks(status="pending"))
        scheduled_reminders = len(self.task_db.list_reminders(status="scheduled"))

        banner = f"""
======================================================
  Project AURA - AI Utility & Response Assistant
  Version: {self.config.version} | Mode: Voice & Command
======================================================
  Workspace  : {self.config.workspace_dir}
  Voice TTS  : [{tts_state}] (use 'voice on' / 'voice off')
  Voice PTT  : [{stt_state}]
  Wake Word  : [{wake_state}]
  Online AI  : [{ai_state}]
  Web Search : [{search_state}]
  Tasks / Rem: [{pending_tasks} pending / {scheduled_reminders} scheduled]
  Hint       : Type 'help' for commands, 'exit' to quit.
------------------------------------------------------
"""
        print(banner.strip())

    def run_hands_free_wake_loop(self) -> None:
        """Run hands-free wake word listening loop with visible state indicators."""
        print(f"\n[WAKE WORD: ACTIVE - Listening for '{self.wakeword.wake_word}'...]")
        print("[Press Ctrl+C or say 'stop listening' to return to command prompt]\n")

        while self.wakeword.is_enabled():
            try:
                detected = self.wakeword.listen_for_wake_word(timeout=3.0)
                if not detected:
                    continue

                print(f"\n[WAKE WORD DETECTED: '{self.wakeword.wake_word.upper()}']")
                if self.tts.enabled:
                    self.tts.speak("Yes, I am listening.")

                transcription, err = self.stt.listen_and_transcribe()
                if err:
                    print(f"\n{err}")
                    continue

                if not transcription:
                    continue

                print(f"\nYou (Voice) > {transcription}")
                if transcription.lower() in ("stop listening", "stop wake word", "pause wake word"):
                    print("[Exiting hands-free wake loop]")
                    break

                # Suppress wake word while speaking response
                self.wakeword.pause()
                try:
                    response, should_exit = self.router.execute(transcription)
                    print(response)
                    if self.tts.enabled:
                        self.tts.speak(response)
                    if should_exit:
                        return
                finally:
                    self.wakeword.resume()

                print(f"\n[WAKE WORD: ACTIVE - Listening for '{self.wakeword.wake_word}'...]")

            except KeyboardInterrupt:
                print("\n[Hands-free wake loop stopped by user]")
                break

    def run(self) -> None:
        """Start the interactive command loop."""
        self.logger.info("Starting AURA interactive session.")
        self.scheduler.start()
        self.print_banner()

        try:
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

                # Hands-free continuous wake-word listening loop
                if trimmed.lower() in ("listen wake", "listen loop", "wake listen", "voice loop"):
                    if not self.wakeword.is_enabled():
                        self.wakeword.set_enabled(True)
                    self.run_hands_free_wake_loop()
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
                    self.wakeword.pause()
                    try:
                        self.tts.speak(response)
                    finally:
                        self.wakeword.resume()

                if should_exit:
                    self.logger.info("Session closed normally.")
                    break
        finally:
            self.scheduler.stop()


def main() -> int:
    """Entry point for the application."""
    app = AuraApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
