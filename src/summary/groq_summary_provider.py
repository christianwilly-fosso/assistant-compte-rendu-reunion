"""Groq-powered summary provider (Llama 3.3 70B)."""

from __future__ import annotations

import logging

from src.reports.report_model import MeetingReport
from src.summary.llm_report_parser import (
    LLMResponseError,
    build_meeting_prompt,
    parse_meeting_report_json,
)
from src.summary.summary_provider import SummaryError, SummaryProvider

_LOGGER = logging.getLogger(__name__)

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_TEMPERATURE = 0.3
_MAX_TOKENS = 4096


class GroqSummaryProvider(SummaryProvider):
    """Calls Groq's chat completion API to produce a structured report."""

    def __init__(self, api_key: str, model_name: str = _DEFAULT_MODEL) -> None:
        if not api_key:
            raise SummaryError("Clé Groq absente : le mode IA est désactivé.")
        try:
            from groq import Groq
        except ImportError as error:  # pragma: no cover - optional dependency
            raise SummaryError("Le module groq n'est pas installé.") from error

        self._client = Groq(api_key=api_key)
        self._model_name = model_name

    def generate_report(self, transcription: str) -> MeetingReport:
        prompt = build_meeting_prompt(transcription)
        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un assistant qui répond uniquement avec du JSON valide.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=_TEMPERATURE,
                max_tokens=_MAX_TOKENS,
            )
        except Exception as error:  # noqa: BLE001 - Groq SDK raises various exceptions
            _LOGGER.exception("Appel Groq échoué")
            raise SummaryError(
                "Le résumé via Groq a échoué. Réessayez ou utilisez le mode algorithmique."
            ) from error

        payload = _extract_text(response)
        try:
            return parse_meeting_report_json(payload, transcription)
        except LLMResponseError as error:
            raise SummaryError(str(error)) from error


def _extract_text(response) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        raise SummaryError("Réponse Groq vide.")
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None) if message else None
    if not content:
        raise SummaryError("Réponse Groq sans contenu.")
    return content
