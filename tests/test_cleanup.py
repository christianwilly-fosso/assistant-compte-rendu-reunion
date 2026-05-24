from __future__ import annotations

from pathlib import Path

from src.shared.cleanup import cleanup_files


def test_cleanup_removes_existing_files(tmp_path):
    file_a = tmp_path / "a.wav"
    file_b = tmp_path / "b.wav"
    file_a.write_bytes(b"x")
    file_b.write_bytes(b"y")

    cleanup_files([str(file_a), str(file_b)])

    assert not file_a.exists()
    assert not file_b.exists()


def test_cleanup_ignores_missing_files(tmp_path):
    missing = tmp_path / "missing.wav"
    cleanup_files([str(missing)])  # ne doit pas lever


def test_cleanup_accepts_none_entries():
    cleanup_files([None])  # ne doit pas lever


def test_cleanup_accepts_path_objects(tmp_path):
    file_path = tmp_path / "x.wav"
    file_path.write_bytes(b"x")
    cleanup_files([Path(file_path)])
    assert not file_path.exists()
