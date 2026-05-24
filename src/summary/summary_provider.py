"""Abstract summary provider — both heuristic and Gemini implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.reports.report_model import MeetingReport


class SummaryError(RuntimeError):
    """Raised when a summary provider cannot produce a report."""


class SummaryProvider(ABC):
    """Builds a :class:`MeetingReport` from a raw transcription."""

    @abstractmethod
    def generate_report(self, transcription: str) -> MeetingReport:
        """Return a fully populated meeting report."""
