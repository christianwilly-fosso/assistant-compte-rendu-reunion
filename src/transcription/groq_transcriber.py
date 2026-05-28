"""Groq-powered transcription (Whisper Large V3, cloud inference)."""

from __future__ import annotations

import logging
from pathlib import Path

from src.transcription.transcriber import Transcriber, TranscriptionError

_LOGGER = logging.getLogger(__name__)

_MAX_FILE_SIZE_MB = 100  # Groq hard limit on audio uploads
_BYTES_PER_MB = 1024 * 1024


class GroqTranscriber(Transcriber):
    """Transcribes audio via Groq's Whisper Large V3 endpoint.

    Cloud inference. Much faster and more accurate than CPU-bound
    faster-whisper on small Spaces. The ``model_size`` argument is
    accepted for interface compatibility but ignored — Groq always
    runs the same Whisper Large V3 weights.
    """

    DEFAULT_MODEL = "whisper-large-v3"

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL) -> None:
        if not api_key:
            raise TranscriptionError("Clé Groq absente : transcription Groq désactivée.")
        try:
            from groq import Groq
        except ImportError as error:  # pragma: no cover - optional dependency
            raise TranscriptionError(
                "Le module groq n'est pas installé."
            ) from error

        self._client = Groq(api_key=api_key)
        self._model_name = model_name

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        model_size: str | None = None,  # noqa: ARG002 - kept for interface compat
    ) -> str:
        path = Path(audio_path)
        self._assert_within_size_limit(path)

        try:
            with path.open("rb") as audio:
                response = self._client.audio.transcriptions.create(
                    file=(path.name, audio.read()),
                    model=self._model_name,
                    language=language,
                    response_format="text",
                    temperature=0.0,
                )
        except Exception as error:  # noqa: BLE001 - Groq SDK raises various exceptions
            _LOGGER.exception("Transcription Groq échouée")
            raise TranscriptionError(
                "La transcription Groq a échoué. Vérifiez votre clé GROQ_API_KEY "
                "ou réessayez avec un fichier plus court."
            ) from error

        return _extract_text(response).strip()

    @staticmethod
    def _assert_within_size_limit(path: Path) -> None:
        if not path.exists():
            raise TranscriptionError("Fichier audio introuvable pour la transcription.")
        size_mb = path.stat().st_size / _BYTES_PER_MB
        if size_mb > _MAX_FILE_SIZE_MB:
            raise TranscriptionError(
                f"Le fichier audio dépasse la limite Groq ({_MAX_FILE_SIZE_MB} Mo). "
                "Réduisez la durée ou utilisez la transcription locale."
            )


def _extract_text(response) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text
    if isinstance(response, str):
        return response
    raise TranscriptionError("Réponse Groq vide ou inattendue.")
