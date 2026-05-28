"""Gemini-powered summary provider (optional)."""

from __future__ import annotations

import logging
from typing import Any

from src.reports.report_model import MeetingReport
from src.summary.llm_report_parser import (
    LLMResponseError,
    build_meeting_prompt,
    parse_meeting_report_json,
)
from src.summary.summary_provider import SummaryError, SummaryProvider

_LOGGER = logging.getLogger(__name__)


class GeminiSummaryProvider(SummaryProvider):
    """Calls Google's Gemini API to produce a structured meeting report.

    The provider is optional: if it cannot be constructed, the caller is
    expected to fall back to :class:`HeuristicSummaryProvider`.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        if not api_key:
            raise SummaryError("Clé Gemini absente : le mode IA est désactivé.")
        try:
            import google.generativeai as genai
        except ImportError as error:  # pragma: no cover - optional dependency
            raise SummaryError(
                "Le module google-generativeai n'est pas installé."
            ) from error

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    def generate_report(self, transcription: str) -> MeetingReport:
        prompt = build_meeting_prompt(transcription)
        try:
            response = self._model.generate_content(prompt)
        except Exception as error:  # noqa: BLE001 - Gemini SDK raises various exceptions
            _LOGGER.exception("Appel Gemini échoué")
            raise SummaryError(
                "Le résumé via Gemini a échoué. Réessayez ou utilisez le mode algorithmique."
            ) from error

        payload = _extract_text(response)
        try:
            return parse_meeting_report_json(payload, transcription)
        except LLMResponseError as error:
            raise SummaryError(str(error)) from error


def _extract_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            value = getattr(part, "text", None)
            if value:
                return value
    raise SummaryError("Réponse Gemini vide.")
