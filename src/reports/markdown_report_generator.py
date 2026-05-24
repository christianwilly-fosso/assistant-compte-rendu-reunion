"""Render a :class:`MeetingReport` as a Markdown document."""

from __future__ import annotations

from src.reports.report_model import ActionItem, MeetingReport, UNSPECIFIED


class MarkdownReportGenerator:
    """Produces the long-form Markdown compte rendu."""

    def generate(self, report: MeetingReport) -> str:
        sections = [
            "# Compte rendu de réunion",
            "",
            "## Informations générales",
            "",
            f"- Date : {report.date or UNSPECIFIED}",
            f"- Participants : {self._format_participants(report.participants)}",
            f"- Sujet : {report.subject or UNSPECIFIED}",
            "",
            "## Résumé exécutif",
            "",
            (report.executive_summary or UNSPECIFIED).strip(),
            "",
            "## Points discutés",
            "",
            self._format_numbered_list(report.discussed_points),
            "",
            "## Décisions prises",
            "",
            self._format_numbered_list(report.decisions),
            "",
            "## Actions à faire",
            "",
            self._format_actions_table(report.action_items),
            "",
            "## Points en suspens",
            "",
            self._format_numbered_list(report.pending_points),
            "",
            "## Transcription complète",
            "",
            (report.full_transcription or UNSPECIFIED).strip(),
            "",
        ]
        return "\n".join(sections).strip() + "\n"

    @staticmethod
    def _format_participants(participants: list[str]) -> str:
        cleaned = [participant.strip() for participant in participants if participant.strip()]
        return ", ".join(cleaned) if cleaned else UNSPECIFIED

    @staticmethod
    def _format_numbered_list(items: list[str]) -> str:
        cleaned = [item.strip() for item in items if item.strip()]
        if not cleaned:
            return UNSPECIFIED
        return "\n".join(f"{index}. {item}" for index, item in enumerate(cleaned, start=1))

    @staticmethod
    def _format_actions_table(actions: list[ActionItem]) -> str:
        header = (
            "| Action | Responsable | Échéance | Statut |\n"
            "|---|---|---|---|"
        )
        if not actions:
            return header + f"\n| {UNSPECIFIED} | {UNSPECIFIED} | {UNSPECIFIED} | {UNSPECIFIED} |"

        rows = [
            "| {action} | {responsible} | {due} | {status} |".format(
                action=_safe(action.description),
                responsible=_safe(action.responsible),
                due=_safe(action.due_date),
                status=_safe(action.status or "À faire"),
            )
            for action in actions
        ]
        return header + "\n" + "\n".join(rows)


def _safe(value: str | None) -> str:
    if value is None or not str(value).strip():
        return UNSPECIFIED
    return str(value).strip().replace("|", "\\|")
