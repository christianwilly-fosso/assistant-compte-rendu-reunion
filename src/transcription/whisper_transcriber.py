"""faster-whisper based implementation of :class:`Transcriber`."""

from __future__ import annotations

import logging
from typing import Any

from src.transcription.transcriber import Transcriber, TranscriptionError

_LOGGER = logging.getLogger(__name__)

_ALLOWED_MODEL_SIZES = ("tiny", "base", "small", "medium", "large")


class WhisperTranscriber(Transcriber):
    """Transcribes audio with `faster-whisper` on CPU by default.

    Models are loaded lazily and cached by size, so calling
    :meth:`transcribe` multiple times with the same model only loads it once.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self._default_model_size = self._normalise_model_size(model_size)
        self._device = device
        self._compute_type = compute_type
        self._model_cache: dict[str, Any] = {}

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        model_size: str | None = None,
    ) -> str:
        effective_model = self._normalise_model_size(model_size or self._default_model_size)
        model = self._load_model(effective_model)
        try:
            segments, _info = model.transcribe(
                audio_path,
                language=language,
                vad_filter=True,
                beam_size=5,
            )
            return self._concatenate_segments(segments)
        except Exception as error:  # noqa: BLE001 - we wrap any backend error
            _LOGGER.exception("Échec de la transcription")
            raise TranscriptionError(
                "La transcription a échoué. Réessayez avec un fichier plus court ou un autre modèle."
            ) from error

    def _load_model(self, model_size: str) -> Any:
        cached = self._model_cache.get(model_size)
        if cached is not None:
            return cached
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:  # pragma: no cover - dependency required at runtime
            raise TranscriptionError(
                "Le module faster-whisper n'est pas installé."
            ) from error

        _LOGGER.info(
            "Chargement du modèle Whisper '%s' (device=%s, compute_type=%s)",
            model_size, self._device, self._compute_type,
        )
        model = WhisperModel(
            model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        self._model_cache[model_size] = model
        return model

    @staticmethod
    def _normalise_model_size(model_size: str) -> str:
        candidate = (model_size or "base").strip().lower()
        if candidate not in _ALLOWED_MODEL_SIZES:
            return "base"
        return candidate

    @staticmethod
    def _concatenate_segments(segments: Any) -> str:
        parts: list[str] = []
        for segment in segments:
            text = (getattr(segment, "text", "") or "").strip()
            if text:
                parts.append(text)
        return " ".join(parts).strip()
