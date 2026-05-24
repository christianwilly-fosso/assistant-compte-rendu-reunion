from __future__ import annotations

from src.summary.heuristic_summary_provider import HeuristicSummaryProvider


def _provider() -> HeuristicSummaryProvider:
    return HeuristicSummaryProvider()


def test_empty_transcription_returns_empty_report():
    report = _provider().generate_report("")
    assert report.full_transcription == ""
    assert report.decisions == []
    assert report.action_items == []


def test_decision_keywords_are_extracted():
    text = (
        "Nous avons parlé du planning. "
        "On a décidé de livrer en deux phases. "
        "La météo est correcte."
    )
    report = _provider().generate_report(text)
    assert any("décidé" in decision.lower() for decision in report.decisions)


def test_action_keywords_are_extracted_with_responsible_and_due_date():
    text = (
        "Marc présente le projet. "
        "Il faut envoyer la proposition à Claire avant le 15 juin. "
        "On clôture la réunion."
    )
    report = _provider().generate_report(text)
    assert report.action_items, "Une action devrait être détectée"
    action = report.action_items[0]
    assert "envoyer" in action.description.lower()
    assert action.due_date is not None
    assert "15" in action.due_date


def test_pending_keywords_are_extracted():
    text = (
        "Le budget reste à discuter. "
        "On valide la date du prochain comité."
    )
    report = _provider().generate_report(text)
    assert any("discuter" in pending.lower() for pending in report.pending_points)


def test_executive_summary_is_non_empty_on_real_text():
    text = (
        "L'équipe produit présente les nouvelles fonctionnalités. "
        "Les utilisateurs demandent plus de rapidité. "
        "Le marketing prépare la communication. "
        "Nous avons décidé de prioriser la performance."
    )
    report = _provider().generate_report(text)
    assert report.executive_summary
    assert len(report.executive_summary) > 0


def test_subject_is_inferred_from_first_sentence():
    text = "Réunion mensuelle de l'équipe produit. Nous évoquons les retours utilisateurs."
    report = _provider().generate_report(text)
    assert report.subject is not None
    assert "Réunion" in report.subject
