"""Plain-text file exporter."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path


class TextExporter:
    """Persists raw text content to a temporary ``.txt`` file."""

    @staticmethod
    def export(content: str, suggested_name: str = "compte_rendu") -> str:
        path = Path(tempfile.gettempdir()) / f"{suggested_name}_{uuid.uuid4().hex}.txt"
        path.write_text(content, encoding="utf-8")
        return str(path)


class MarkdownExporter:
    """Persists Markdown content to a temporary ``.md`` file."""

    @staticmethod
    def export(content: str, suggested_name: str = "compte_rendu") -> str:
        path = Path(tempfile.gettempdir()) / f"{suggested_name}_{uuid.uuid4().hex}.md"
        path.write_text(content, encoding="utf-8")
        return str(path)
