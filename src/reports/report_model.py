"""Domain model for a meeting report."""

from __future__ import annotations

from dataclasses import dataclass, field

UNSPECIFIED = "Non précisé"


@dataclass(frozen=True)
class ActionItem:
    """A concrete action extracted from a meeting."""

    description: str
    responsible: str | None = None
    due_date: str | None = None
    status: str | None = "À faire"


@dataclass(frozen=True)
class MeetingReport:
    """A structured meeting report ready to be rendered."""

    title: str = "Compte rendu de réunion"
    date: str | None = None
    participants: list[str] = field(default_factory=list)
    subject: str | None = None
    executive_summary: str = ""
    discussed_points: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    pending_points: list[str] = field(default_factory=list)
    full_transcription: str = ""
    whatsapp_summary: str = ""
