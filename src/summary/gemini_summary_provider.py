"""Gemini-powered summary provider (optional)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from src.reports.report_model import ActionItem, MeetingReport
from src.summary.summary_provider import SummaryError, SummaryProvider

_LOGGER = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """Tu es un assistant professionnel de compte rendu de réunion.

À partir de la transcription ci-dessous, produis un compte rendu clair en français.

Contraintes :
- Corrige le français sans inventer d'information.
- Ne crée pas de décision ou d'action si elle n'est pas dans la transcription.
- Si une information est absente, écris "Non précisé".
- Réponds STRICTEMENT en JSON valide selon le schéma ci-dessous, sans aucun texte avant ou après.

Schéma JSON attendu :
{{
  "title": "string",
  "date": "string ou null",
  "participants": ["string"],
  "subject": "string ou null",
  "executive_summary": "string",
  "discussed_points": ["string"],
  "decisions": ["string"],
  "action_items": [
    {{
      "description": "string",
      "responsible": "string ou null",
      "due_date": "string ou null",
      "status": "string ou null"
    }}
  ],
  "pending_points": ["string"],
  "whatsapp_summary": "string"
}}

Transcription :
{transcription}
"""


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
        prompt = _PROMPT_TEMPLATE.format(transcription=transcription)
        try:
            response = self._model.generate_content(prompt)
        except Exception as error:  # noqa: BLE001 - Gemini SDK raises various exceptions
            _LOGGER.exception("Appel Gemini échoué")
            raise SummaryError(
                "Le résumé via Gemini a échoué. Réessayez ou utilisez le mode algorithmique."
            ) from error

        payload = _extract_text(response)
        data = _safe_json_parse(payload)
        return _build_report(data, transcription)


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


def _safe_json_parse(payload: str) -> dict:
    cleaned = payload.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, count=1).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        _LOGGER.error("JSON Gemini invalide : %s", cleaned[:200])
        raise SummaryError("Réponse Gemini non exploitable (JSON invalide).") from error


def _build_report(data: dict, transcription: str) -> MeetingReport:
    actions_raw = data.get("action_items") or []
    actions = [
        ActionItem(
            description=str(item.get("description", "")).strip(),
            responsible=_optional_str(item.get("responsible")),
            due_date=_optional_str(item.get("due_date")),
            status=_optional_str(item.get("status")) or "À faire",
        )
        for item in actions_raw
        if isinstance(item, dict) and item.get("description")
    ]
    return MeetingReport(
        title=str(data.get("title") or "Compte rendu de réunion"),
        date=_optional_str(data.get("date")),
        participants=_string_list(data.get("participants")),
        subject=_optional_str(data.get("subject")),
        executive_summary=str(data.get("executive_summary") or "").strip(),
        discussed_points=_string_list(data.get("discussed_points")),
        decisions=_string_list(data.get("decisions")),
        action_items=actions,
        pending_points=_string_list(data.get("pending_points")),
        full_transcription=transcription,
        whatsapp_summary=str(data.get("whatsapp_summary") or "").strip(),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"non précisé", "non precise", "null", "none"}:
        return None
    return text


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
