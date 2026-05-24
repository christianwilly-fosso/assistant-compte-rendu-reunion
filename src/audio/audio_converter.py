"""Audio normalisation to mono 16 kHz WAV via FFmpeg."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

_TARGET_SAMPLE_RATE = 16_000
_TARGET_CHANNELS = 1
_FFMPEG_TIMEOUT_SECONDS = 600


class AudioConversionError(RuntimeError):
    """Raised when FFmpeg fails to produce a usable output."""


def convert_to_wav(
    input_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str] | None = None,
) -> str:
    """Convert any supported audio file into a mono 16 kHz WAV.

    Returns the absolute path to the generated WAV file. The caller is
    responsible for removing it (typically via :func:`cleanup_files`).
    """
    source = Path(input_path)
    if not source.exists():
        raise AudioConversionError(f"Fichier source introuvable : {source}")

    _ensure_ffmpeg_available()
    target_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir())
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"meeting_{uuid.uuid4().hex}.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i", str(source),
        "-ar", str(_TARGET_SAMPLE_RATE),
        "-ac", str(_TARGET_CHANNELS),
        "-vn",
        str(output_path),
    ]
    _run_ffmpeg(command)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise AudioConversionError("FFmpeg n'a pas produit de fichier audio exploitable.")
    return str(output_path)


def _ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise AudioConversionError(
            "FFmpeg n'est pas installé sur ce système. "
            "Installez FFmpeg pour permettre la conversion audio."
        )


def _run_ffmpeg(command: list[str]) -> None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=_FFMPEG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise AudioConversionError(
            "La conversion audio a dépassé le délai autorisé."
        ) from error

    if completed.returncode != 0:
        _LOGGER.error("Échec FFmpeg : %s", completed.stderr.strip())
        raise AudioConversionError(
            "Impossible de convertir le fichier audio. "
            "Vérifiez le format et l'intégrité du fichier."
        )
