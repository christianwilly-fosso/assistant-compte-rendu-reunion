"""PDF export of a meeting report using ReportLab."""

from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path

from src.reports.report_model import ActionItem, MeetingReport, UNSPECIFIED

_LOGGER = logging.getLogger(__name__)


class PdfExporter:
    """Persist a :class:`MeetingReport` as a PDF.

    Falls back to ``None`` (and a warning) if ReportLab is not installed.
    """

    def export(self, report: MeetingReport, suggested_name: str = "compte_rendu") -> str | None:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError:
            _LOGGER.warning("reportlab n'est pas installé : export PDF désactivé.")
            return None

        path = Path(tempfile.gettempdir()) / f"{suggested_name}_{uuid.uuid4().hex}.pdf"
        document = SimpleDocTemplate(str(path), pagesize=A4, title="Compte rendu de réunion")
        styles = getSampleStyleSheet()
        story = []

        def heading(text: str) -> None:
            story.append(Paragraph(text, styles["Heading2"]))

        def paragraph(text: str) -> None:
            story.append(Paragraph(_escape(text), styles["BodyText"]))
            story.append(Spacer(1, 6))

        story.append(Paragraph("Compte rendu de réunion", styles["Heading1"]))
        story.append(Spacer(1, 12))

        heading("Informations générales")
        paragraph(f"Date : {report.date or UNSPECIFIED}")
        paragraph(
            "Participants : " + (", ".join(report.participants) if report.participants else UNSPECIFIED)
        )
        paragraph(f"Sujet : {report.subject or UNSPECIFIED}")

        heading("Résumé exécutif")
        paragraph(report.executive_summary or UNSPECIFIED)

        _add_numbered(story, heading, paragraph, "Points discutés", report.discussed_points)
        _add_numbered(story, heading, paragraph, "Décisions prises", report.decisions)

        heading("Actions à faire")
        story.append(_build_actions_table(report.action_items, Table, TableStyle, colors))
        story.append(Spacer(1, 12))

        _add_numbered(story, heading, paragraph, "Points en suspens", report.pending_points)

        heading("Transcription complète")
        paragraph(report.full_transcription or UNSPECIFIED)

        document.build(story)
        return str(path)


def _add_numbered(story, heading, paragraph, title: str, items: list[str]) -> None:
    heading(title)
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        paragraph(UNSPECIFIED)
        return
    for index, item in enumerate(cleaned, start=1):
        paragraph(f"{index}. {item}")


def _build_actions_table(actions: list[ActionItem], Table, TableStyle, colors):
    data = [["Action", "Responsable", "Échéance", "Statut"]]
    if not actions:
        data.append([UNSPECIFIED, UNSPECIFIED, UNSPECIFIED, UNSPECIFIED])
    else:
        for action in actions:
            data.append([
                action.description or UNSPECIFIED,
                action.responsible or UNSPECIFIED,
                action.due_date or UNSPECIFIED,
                action.status or "À faire",
            ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )
