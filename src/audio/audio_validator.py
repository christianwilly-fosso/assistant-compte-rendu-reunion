"""Pre-flight checks on user-uploaded audio files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_BYTES_PER_MB = 1024 * 1024


class AudioValidationError(ValueError):
    """Raised when the user-uploaded audio file cannot be processed."""


@dataclass(frozen=True)
class AudioValidator:
    """Validates audio uploads against allowed extensions and a max size."""

    supported_extensions: tuple[str, ...]
    max_size_mb: int

    def validate(self, audio_path: str | os.PathLike[str]) -> Path:
        """Return the validated path or raise :class:`AudioValidationError`."""
        if not audio_path:
            raise AudioValidationError("Aucun fichier audio fourni.")

        path = Path(audio_path)
        if not path.exists() or not path.is_file():
            raise AudioValidationError("Le fichier audio est introuvable.")

        self._assert_supported_extension(path)
        self._assert_within_size_limit(path)
        return path

    def _assert_supported_extension(self, path: Path) -> None:
        extension = path.suffix.lower()
        if extension not in self.supported_extensions:
            allowed = ", ".join(self.supported_extensions)
            raise AudioValidationError(
                f"Format audio non supporté ({extension or 'inconnu'}). "
                f"Formats acceptés : {allowed}."
            )

    def _assert_within_size_limit(self, path: Path) -> None:
        size_mb = path.stat().st_size / _BYTES_PER_MB
        if size_mb > self.max_size_mb:
            raise AudioValidationError(
                f"Le fichier dépasse la taille maximale autorisée "
                f"({self.max_size_mb} Mo). Veuillez compresser ou raccourcir l'audio."
            )
