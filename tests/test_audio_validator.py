from __future__ import annotations

import os

import pytest

from src.audio.audio_validator import AudioValidationError, AudioValidator


@pytest.fixture
def validator() -> AudioValidator:
    return AudioValidator(
        supported_extensions=(".mp3", ".wav", ".m4a"),
        max_size_mb=1,
    )


def _make_audio_file(tmp_path, name: str, size_bytes: int = 1024) -> str:
    path = tmp_path / name
    path.write_bytes(b"\0" * size_bytes)
    return str(path)


def test_validate_accepts_supported_extension(tmp_path, validator):
    audio = _make_audio_file(tmp_path, "meeting.mp3")
    assert validator.validate(audio).name == "meeting.mp3"


def test_validate_is_case_insensitive(tmp_path, validator):
    audio = _make_audio_file(tmp_path, "meeting.MP3")
    assert validator.validate(audio).name == "meeting.MP3"


def test_validate_rejects_unsupported_extension(tmp_path, validator):
    audio = _make_audio_file(tmp_path, "meeting.exe")
    with pytest.raises(AudioValidationError, match="non supporté"):
        validator.validate(audio)


def test_validate_rejects_oversize_file(tmp_path, validator):
    audio = _make_audio_file(tmp_path, "huge.wav", size_bytes=2 * 1024 * 1024)
    with pytest.raises(AudioValidationError, match="taille"):
        validator.validate(audio)


def test_validate_rejects_missing_file(validator):
    with pytest.raises(AudioValidationError, match="introuvable"):
        validator.validate("/tmp/does_not_exist__.mp3")


def test_validate_rejects_empty_path(validator):
    with pytest.raises(AudioValidationError, match="Aucun fichier"):
        validator.validate("")
