"""Render a short, WhatsApp-friendly version of a meeting report."""

from __future__ import annotations

from src.reports.report_model import ActionItem, MeetingReport, UNSPECIFIED


class WhatsAppReportGenerator:
    """Produces a compact summary optimised for chat sharing."""

    def generate(self, report: MeetingReport) -> str:
        if report.whatsapp_summary and report.whatsapp_summary.strip():
            return report.whatsapp_summary.strip()

        lines = [
            "📝 Compte rendu de réunion",
            "",
            "📌 Sujet :",
            report.subject or UNSPECIFIED,
            "",
            "✅ Résumé :",
            (report.executive_summary or UNSPECIFIED).strip(),
            "",
            "📍 Décisions :",
            *self._numbered(report.decisions),
            "",
            "📋 Actions :",
            *self._actions(report.action_items),
            "",
            "❓ Points en suspens :",
            *self._bulleted(report.pending_points),
        ]
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _numbered(items: list[str]) -> list[str]:
        cleaned = [item.strip() for item in items if item.strip()]
        if not cleaned:
            return [f"- {UNSPECIFIED}"]
        return [f"{index}. {item}" for index, item in enumerate(cleaned, start=1)]

    @staticmethod
    def _bulleted(items: list[str]) -> list[str]:
        cleaned = [item.strip() for item in items if item.strip()]
        if not cleaned:
            return [f"- {UNSPECIFIED}"]
        return [f"- {item}" for item in cleaned]

    @staticmethod
    def _actions(actions: list[ActionItem]) -> list[str]:
        if not actions:
            return [f"- {UNSPECIFIED}"]
        rendered: list[str] = []
        for action in actions:
            responsible = action.responsible or UNSPECIFIED
            due = action.due_date or UNSPECIFIED
            rendered.append(
                f"- {action.description} — Responsable : {responsible} — Échéance : {due}"
            )
        return rendered
