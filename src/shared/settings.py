"""Centralised application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is an optional convenience
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


DEFAULT_WHISPER_MODEL = "base"
DEFAULT_WHISPER_DEVICE = "cpu"
DEFAULT_WHISPER_COMPUTE_TYPE = "int8"
DEFAULT_MAX_AUDIO_SIZE_MB = 100
DEFAULT_SUPPORTED_EXTENSIONS = (".m4a", ".mp3", ".ogg", ".wav", ".webm", ".flac", ".aac")
DEFAULT_SUMMARY_MODE = "auto"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_WHISPER_MODEL = "whisper-large-v3"


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings.

    All defaults guarantee the application can run without any API key
    and without any extra environment variable. Gemini is enabled only
    when ``gemini_api_key`` is provided.
    """

    whisper_model_size: str = DEFAULT_WHISPER_MODEL
    whisper_device: str = DEFAULT_WHISPER_DEVICE
    whisper_compute_type: str = DEFAULT_WHISPER_COMPUTE_TYPE
    max_audio_size_mb: int = DEFAULT_MAX_AUDIO_SIZE_MB
    supported_extensions: tuple[str, ...] = field(default_factory=lambda: DEFAULT_SUPPORTED_EXTENSIONS)
    summary_mode: str = DEFAULT_SUMMARY_MODE
    gemini_api_key: str | None = None
    gemini_model: str = DEFAULT_GEMINI_MODEL
    groq_api_key: str | None = None
    groq_chat_model: str = DEFAULT_GROQ_CHAT_MODEL
    groq_whisper_model: str = DEFAULT_GROQ_WHISPER_MODEL

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables (and ``.env`` if present)."""
        load_dotenv()
        return cls(
            whisper_model_size=os.getenv("WHISPER_MODEL_SIZE", DEFAULT_WHISPER_MODEL),
            whisper_device=os.getenv("WHISPER_DEVICE", DEFAULT_WHISPER_DEVICE),
            whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", DEFAULT_WHISPER_COMPUTE_TYPE),
            max_audio_size_mb=_read_int("MAX_AUDIO_SIZE_MB", DEFAULT_MAX_AUDIO_SIZE_MB),
            supported_extensions=DEFAULT_SUPPORTED_EXTENSIONS,
            summary_mode=os.getenv("SUMMARY_MODE", DEFAULT_SUMMARY_MODE),
            gemini_api_key=_clean(os.getenv("GEMINI_API_KEY")),
            gemini_model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            groq_api_key=_clean(os.getenv("GROQ_API_KEY")),
            groq_chat_model=os.getenv("GROQ_CHAT_MODEL", DEFAULT_GROQ_CHAT_MODEL),
            groq_whisper_model=os.getenv("GROQ_WHISPER_MODEL", DEFAULT_GROQ_WHISPER_MODEL),
        )

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def groq_enabled(self) -> bool:
        return bool(self.groq_api_key)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
