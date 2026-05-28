from __future__ import annotations

import json

import pytest

from src.summary.llm_report_parser import (
    LLMResponseError,
    build_meeting_prompt,
    parse_meeting_report_json,
)


_VALID_PAYLOAD = {
    "title": "Réunion produit",
    "date": "2026-05-28",
    "participants": ["Alice", "Bob"],
    "subject": "Lancement",
    "executive_summary": "On parle du lancement.",
    "discussed_points": ["Planning", "Budget"],
    "decisions": ["Livraison en deux phases"],
    "action_items": [
        {
            "description": "Envoyer la proposition",
            "responsible": "Alice",
            "due_date": "15 juin",
            "status": "À faire",
        }
    ],
    "pending_points": ["Stratégie marketing"],
    "whatsapp_summary": "Réunion produit OK",
}


def test_build_meeting_prompt_embeds_transcription():
    prompt = build_meeting_prompt("Salut tout le monde.")
    assert "Salut tout le monde." in prompt
    assert "Schéma JSON attendu" in prompt


def test_parse_valid_json_returns_complete_report():
    report = parse_meeting_report_json(json.dumps(_VALID_PAYLOAD), "Transcription")
    assert report.title == "Réunion produit"
    assert report.date == "2026-05-28"
    assert report.participants == ["Alice", "Bob"]
    assert report.executive_summary == "On parle du lancement."
    assert report.decisions == ["Livraison en deux phases"]
    assert len(report.action_items) == 1
    assert report.action_items[0].responsible == "Alice"
    assert report.full_transcription == "Transcription"


def test_parse_strips_markdown_code_fences():
    fenced = f"```json\n{json.dumps(_VALID_PAYLOAD)}\n```"
    report = parse_meeting_report_json(fenced, "T")
    assert report.title == "Réunion produit"


def test_parse_strips_unlabeled_code_fences():
    fenced = f"```\n{json.dumps(_VALID_PAYLOAD)}\n```"
    report = parse_meeting_report_json(fenced, "T")
    assert report.title == "Réunion produit"


def test_parse_treats_non_precise_as_none():
    payload = {**_VALID_PAYLOAD, "date": "Non précisé", "subject": "null"}
    report = parse_meeting_report_json(json.dumps(payload), "T")
    assert report.date is None
    assert report.subject is None


def test_parse_filters_empty_actions():
    payload = {
        **_VALID_PAYLOAD,
        "action_items": [
            {"description": "", "responsible": "X"},
            {"description": "Vraie action", "responsible": "Y"},
        ],
    }
    report = parse_meeting_report_json(json.dumps(payload), "T")
    assert len(report.action_items) == 1
    assert report.action_items[0].description == "Vraie action"


def test_parse_invalid_json_raises():
    with pytest.raises(LLMResponseError, match="JSON invalide"):
        parse_meeting_report_json("not json at all", "T")


def test_parse_empty_payload_raises():
    with pytest.raises(LLMResponseError, match="vide"):
        parse_meeting_report_json("", "T")


def test_parse_array_payload_raises():
    with pytest.raises(LLMResponseError, match="objet JSON"):
        parse_meeting_report_json("[1, 2, 3]", "T")


def test_parse_assigns_default_status_when_missing():
    payload = {**_VALID_PAYLOAD, "action_items": [
        {"description": "Tâche sans statut", "responsible": None, "due_date": None}
    ]}
    report = parse_meeting_report_json(json.dumps(payload), "T")
    assert report.action_items[0].status == "À faire"
