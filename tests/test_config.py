"""Tests for config persistence (API key, provider, model)."""

from pathlib import Path

import pytest

from janett import config


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point config storage at a temp dir and clear the env override."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_api_key_round_trip() -> None:
    assert config.get_openai_api_key() is None
    config.set_openai_api_key("sk-test-123")
    assert config.get_openai_api_key() == "sk-test-123"


def test_env_var_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    config.set_openai_api_key("from-file")
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    assert config.get_openai_api_key() == "from-env"


def test_provider_persistence() -> None:
    # Defaults to the configured default before anything is saved.
    assert config.get_saved_provider() == config.DEFAULT_PROVIDER
    config.set_saved_provider("openai")
    assert config.get_saved_provider() == "openai"


def test_unknown_saved_provider_falls_back() -> None:
    config.set_saved_provider("bogus")
    assert config.get_saved_provider() == config.DEFAULT_PROVIDER


def test_model_persistence() -> None:
    assert config.get_saved_model() is None
    config.set_saved_model("gpt-4o")
    assert config.get_saved_model() == "gpt-4o"


def test_settings_coexist() -> None:
    config.set_openai_api_key("sk-x")
    config.set_saved_provider("openai")
    config.set_saved_model("gpt-4o")
    assert config.get_openai_api_key() == "sk-x"
    assert config.get_saved_provider() == "openai"
    assert config.get_saved_model() == "gpt-4o"


def test_get_model_pricing_known_and_unknown() -> None:
    openai_pricing = config.get_model_pricing("gpt-4o-mini")
    assert openai_pricing["input"] > 0

    ollama_pricing = config.get_model_pricing("llama3.2")
    assert ollama_pricing["input"] == 0.0
    assert ollama_pricing["output"] == 0.0
    assert ollama_pricing["context"] == config.DEFAULT_CONTEXT_LIMIT
