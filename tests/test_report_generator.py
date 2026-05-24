from __future__ import annotations

from src.reports.markdown_report_generator import MarkdownReportGenerator
from src.reports.report_model import ActionItem, MeetingReport, UNSPECIFIED
from src.reports.whatsapp_report_generator import WhatsAppReportGenerator


def _sample_report() -> MeetingReport:
    return MeetingReport(
        title="Compte rendu de réunion",
        date="2026-05-24",
        participants=["Alice", "Bob"],
        subject="Lancement du produit",
        executive_summary="Discussion sur le lancement.",
        discussed_points=["Planning", "Budget"],
        decisions=["Livraison en deux phases"],
        action_items=[
            ActionItem(
                description="Envoyer la proposition",
                responsible="Alice",
                due_date="15 juin",
                status="À faire",
            )
        ],
        pending_points=["Stratégie marketing"],
        full_transcription="Transcription complète…",
    )


def test_markdown_report_contains_all_sections():
    markdown = MarkdownReportGenerator().generate(_sample_report())
    for required in (
        "# Compte rendu de réunion",
        "## Informations générales",
        "## Résumé exécutif",
        "## Points discutés",
        "## Décisions prises",
        "## Actions à faire",
        "| Action | Responsable | Échéance | Statut |",
        "## Points en suspens",
        "## Transcription complète",
        "Alice",
        "15 juin",
    ):
        assert required in markdown, f"Section manquante : {required}"


def test_markdown_handles_empty_report():
    markdown = MarkdownReportGenerator().generate(MeetingReport())
    assert UNSPECIFIED in markdown
    assert "## Actions à faire" in markdown


def test_markdown_escapes_pipes_in_table_cells():
    report = MeetingReport(action_items=[
        ActionItem(description="Étape | importante", responsible="Bob")
    ])
    markdown = MarkdownReportGenerator().generate(report)
    assert "Étape \\| importante" in markdown


def test_whatsapp_summary_contains_emojis_and_action():
    whatsapp = WhatsAppReportGenerator().generate(_sample_report())
    assert "📝" in whatsapp
    assert "📌 Sujet :" in whatsapp
    assert "Envoyer la proposition" in whatsapp
    assert "Alice" in whatsapp


def test_whatsapp_uses_explicit_summary_if_provided():
    report = MeetingReport(whatsapp_summary="Texte court ad-hoc")
    whatsapp = WhatsAppReportGenerator().generate(report)
    assert whatsapp.strip() == "Texte court ad-hoc"


def test_whatsapp_handles_empty_lists():
    whatsapp = WhatsAppReportGenerator().generate(MeetingReport())
    assert UNSPECIFIED in whatsapp
