"""Best-effort cleanup of temporary files."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable

_LOGGER = logging.getLogger(__name__)


def cleanup_files(paths: Iterable[str | os.PathLike[str] | None]) -> None:
    """Remove every file in ``paths`` silently.

    Missing files are ignored. Errors are logged but never raised so that
    cleanup never masks the original processing outcome.
    """
    for path in paths:
        if path is None:
            continue
        _remove_silently(Path(path))


def _remove_silently(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except OSError as error:
        _LOGGER.warning("Impossible de supprimer %s : %s", path, error)
