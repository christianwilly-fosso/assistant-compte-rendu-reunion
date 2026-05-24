"""Transcriber abstraction used by the application core."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TranscriptionError(RuntimeError):
    """Raised when transcription fails for any reason."""


class Transcriber(ABC):
    """Abstract interface for any speech-to-text provider.

    Concrete implementations must be substitutable: callers depend only
    on this interface (Dependency Inversion Principle).
    """

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        model_size: str | None = None,
    ) -> str:
        """Return the full transcription text for the given audio file."""
