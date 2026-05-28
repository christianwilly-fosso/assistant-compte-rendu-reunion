"""Shared prompt + JSON → MeetingReport parser used by every LLM provider.

Centralising this keeps every provider (Gemini, Groq, future ones) on the
exact same contract and avoids drift.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from src.reports.report_model import ActionItem, MeetingReport

_LOGGER = logging.getLogger(__name__)

MEETING_REPORT_PROMPT = """Tu es un assistant professionnel de compte rendu de réunion.

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


class LLMResponseError(RuntimeError):
    """Raised when an LLM response cannot be turned into a MeetingReport."""


def build_meeting_prompt(transcription: str) -> str:
    """Return the prompt to send to any compatible LLM."""
    return MEETING_REPORT_PROMPT.format(transcription=transcription)


def parse_meeting_report_json(payload: str, transcription: str) -> MeetingReport:
    """Parse an LLM JSON payload into a :class:`MeetingReport`.

    Strips markdown code fences if present and raises
    :class:`LLMResponseError` on invalid JSON.
    """
    data = _safe_json_parse(payload)
    return _build_report(data, transcription)


def _safe_json_parse(payload: str) -> dict:
    cleaned = (payload or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, count=1).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    if not cleaned:
        raise LLMResponseError("Réponse LLM vide.")
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        _LOGGER.error("JSON LLM invalide : %s", cleaned[:200])
        raise LLMResponseError("Réponse LLM non exploitable (JSON invalide).") from error
    if not isinstance(parsed, dict):
        raise LLMResponseError("Réponse LLM ne contient pas un objet JSON.")
    return parsed


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
        if isinstance(item, dict) and str(item.get("description", "")).strip()
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
