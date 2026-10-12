"""Application orchestrator and interactive command-line loop."""

from __future__ import annotations

import sys
from typing import Optional

from aura.config import AuraConfig
from aura.logging_config import setup_logging
from aura.router import CommandRouter


class AuraApp:
    """Core interactive application runtime for Project AURA."""

    def __init__(self, config: Optional[AuraConfig] = None) -> None:
        self.config = config or AuraConfig.load()
        self.logger = setup_logging(self.config.log_level)
        self.router = CommandRouter(self.config)

    def print_banner(self) -> None:
        """Display startup information and workspace status."""
        banner = f"""
======================================================
  Project AURA - AI Utility & Response Assistant
  Version: {self.config.version} | Mode: Local MVP
======================================================
  Workspace: {self.config.workspace_dir}
  Status   : Ready for input
  Hint     : Type 'help' for commands, 'exit' to quit.
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

            response, should_exit = self.router.execute(user_input)
            print(response)

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
