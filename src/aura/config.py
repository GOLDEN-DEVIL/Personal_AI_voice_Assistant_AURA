"""Configuration management for Project AURA."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Attempt to load python-dotenv if installed
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class AuraConfig:
    """Immutable application configuration."""

    app_name: str
    version: str
    workspace_dir: Path
    log_level: str
    max_preview_rows: int = 5
    max_preview_chars: int = 2000
    tts_enabled: bool = False
    tts_rate: int = 180
    tts_volume: float = 0.9
    stt_timeout: int = 5
    stt_phrase_limit: int = 10
    ai_provider: str = "gemini"
    gemini_api_key: Optional[str] = None
    ai_model: str = "gemini-1.5-flash"
    ai_system_prompt: str = (
        "You are AURA (AI Utility & Response Assistant), a polite, concise, and helpful personal voice assistant. "
        "Provide clear, direct answers under 3-4 sentences when possible."
    )

    @classmethod
    def load(cls) -> AuraConfig:
        """Load configuration from environment variables with sensible defaults."""
        app_name = os.getenv("AURA_APP_NAME", "AURA")
        version = os.getenv("AURA_VERSION", "0.1.0")
        log_level = os.getenv("AURA_LOG_LEVEL", "INFO").upper()

        tts_enabled = os.getenv("AURA_TTS_ENABLED", "false").lower() in ("true", "1", "yes")
        try:
            tts_rate = int(os.getenv("AURA_TTS_RATE", "180"))
        except ValueError:
            tts_rate = 180

        try:
            tts_volume = float(os.getenv("AURA_TTS_VOLUME", "0.9"))
        except ValueError:
            tts_volume = 0.9

        # AI Provider configuration (Stage 4)
        ai_provider = os.getenv("AURA_AI_PROVIDER", "gemini").lower().strip()
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AURA_AI_API_KEY")
        ai_model = os.getenv("AURA_AI_MODEL", "gemini-1.5-flash").strip()
        ai_system_prompt = os.getenv(
            "AURA_AI_SYSTEM_PROMPT",
            "You are AURA (AI Utility & Response Assistant), a polite, concise, and helpful personal voice assistant. "
            "Provide clear, direct answers under 3-4 sentences when possible.",
        )

        # Locate project root (assuming src/aura/config.py -> root is 3 levels up)
        project_root = Path(__file__).resolve().parent.parent.parent

        env_workspace = os.getenv("AURA_WORKSPACE_DIR")
        if env_workspace:
            workspace_path = Path(env_workspace).expanduser().resolve()
        else:
            workspace_path = (project_root / "data").resolve()

        # Ensure directory exists or can be accessed safely
        workspace_path.mkdir(parents=True, exist_ok=True)

        return cls(
            app_name=app_name,
            version=version,
            workspace_dir=workspace_path,
            log_level=log_level,
            tts_enabled=tts_enabled,
            tts_rate=tts_rate,
            tts_volume=tts_volume,
            ai_provider=ai_provider,
            gemini_api_key=gemini_api_key,
            ai_model=ai_model,
            ai_system_prompt=ai_system_prompt,
        )
