"""Logging setup for Project AURA."""

from __future__ import annotations

import logging
import sys


def setup_logging(level_name: str = "INFO") -> logging.Logger:
    """Configure structured logging for AURA."""
    numeric_level = getattr(logging, level_name.upper(), logging.INFO)

    logger = logging.getLogger("aura")
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
