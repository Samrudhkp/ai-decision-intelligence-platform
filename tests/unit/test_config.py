"""Unit tests for Settings (no secrets required)."""

from __future__ import annotations

from src.utils.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
    )
    assert settings.app_name == "decision-intelligence-platform"
    assert settings.api_port == 8000
    assert settings.azure_storage_connection_string in (None, "")
