from __future__ import annotations

import os

import pytest

from src.shared.settings import Settings, DEFAULT_WHISPER_MODEL, DEFAULT_MAX_AUDIO_SIZE_MB


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    for var in (
        "WHISPER_MODEL_SIZE", "WHISPER_DEVICE", "WHISPER_COMPUTE_TYPE",
        "MAX_AUDIO_SIZE_MB", "SUMMARY_MODE",
        "GEMINI_API_KEY", "GEMINI_MODEL",
        "GROQ_API_KEY", "GROQ_CHAT_MODEL", "GROQ_WHISPER_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)
    yield


def test_settings_defaults_when_env_is_empty():
    settings = Settings.load()
    assert settings.whisper_model_size == DEFAULT_WHISPER_MODEL
    assert settings.max_audio_size_mb == DEFAULT_MAX_AUDIO_SIZE_MB
    assert settings.gemini_api_key is None
    assert settings.gemini_enabled is False
    assert settings.groq_api_key is None
    assert settings.groq_enabled is False


def test_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("WHISPER_MODEL_SIZE", "small")
    monkeypatch.setenv("MAX_AUDIO_SIZE_MB", "42")
    monkeypatch.setenv("GEMINI_API_KEY", "sk-test")

    settings = Settings.load()
    assert settings.whisper_model_size == "small"
    assert settings.max_audio_size_mb == 42
    assert settings.gemini_api_key == "sk-test"
    assert settings.gemini_enabled is True


def test_settings_treats_blank_gemini_key_as_disabled(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    settings = Settings.load()
    assert settings.gemini_api_key is None
    assert settings.gemini_enabled is False


def test_settings_falls_back_to_default_on_invalid_integer(monkeypatch):
    monkeypatch.setenv("MAX_AUDIO_SIZE_MB", "not-a-number")
    settings = Settings.load()
    assert settings.max_audio_size_mb == DEFAULT_MAX_AUDIO_SIZE_MB


def test_settings_enables_groq_when_key_present(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    settings = Settings.load()
    assert settings.groq_api_key == "gsk-test"
    assert settings.groq_enabled is True


def test_settings_treats_blank_groq_key_as_disabled(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")
    settings = Settings.load()
    assert settings.groq_api_key is None
    assert settings.groq_enabled is False
