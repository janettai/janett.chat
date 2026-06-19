"""Tests for ChatSession and TokenCounter."""

from pathlib import Path

import pytest

from janett import chat
from janett.chat import ChatSession, TokenCounter

from .conftest import FakeClient


def _session() -> ChatSession:
    return ChatSession(client=FakeClient(""))  # type: ignore[arg-type]


def test_token_counter_counts_tokens() -> None:
    counter = TokenCounter("gpt-4o-mini")
    assert counter.count("") == 0
    assert counter.count("hello world") > 0


def test_token_counter_unknown_model_falls_back() -> None:
    # A non-OpenAI model name must not raise; it falls back to cl100k_base.
    counter = TokenCounter("llama3.2")
    assert counter.count("hello") > 0


def test_count_messages_includes_overhead() -> None:
    counter = TokenCounter("gpt-4o-mini")
    messages = [
        {"role": "system", "content": "be nice"},
        {"role": "user", "content": "hi"},
    ]
    # Per-message overhead (4 each) + trailing 2 guarantees a floor.
    assert counter.count_messages(messages) >= 2 + 4 * len(messages)


def test_clear_history_keeps_system_prompt() -> None:
    session = _session()
    session.add_user_msg("hello")
    session.total_input_tokens = 50
    session.clear_history()

    assert len(session.messages) == 1
    assert session.messages[0]["role"] == "system"
    assert session.total_input_tokens == 0


def test_get_token_stats_shape_and_free_provider() -> None:
    session = ChatSession(provider="ollama", client=FakeClient(""))  # type: ignore[arg-type]
    session.total_input_tokens = 1000
    session.total_output_tokens = 1000
    stats = session.get_token_stats()

    assert stats["total_tokens"] == 2000
    # Ollama is free: costs are reported as zero rather than guessed.
    assert stats["total_cost"] == 0.0
    assert set(stats) >= {
        "model",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "total_cost",
        "context_used",
        "context_limit",
    }


def test_get_token_stats_openai_has_cost() -> None:
    session = ChatSession(
        model="gpt-4o-mini",
        provider="openai",
        client=FakeClient(""),  # type: ignore[arg-type]
    )
    session.total_input_tokens = 1_000_000
    stats = session.get_token_stats()
    assert stats["input_cost"] == pytest.approx(0.15)


def test_save_and_load_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(chat, "SAVE_DIR", tmp_path)

    session = _session()
    session.add_user_msg("question")
    session.add_assistant_message("answer")

    path = session.save_conversation("mychat")
    assert path is not None
    assert (tmp_path / "mychat.json").exists()

    loaded = ChatSession(client=FakeClient(""))  # type: ignore[arg-type]
    assert loaded.load_conversation("mychat") is True
    # System prompt + the two restored messages.
    assert loaded.get_message_count() == 2
    assert loaded.messages[1]["content"] == "question"


def test_load_missing_returns_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(chat, "SAVE_DIR", tmp_path)
    session = _session()
    assert session.load_conversation("does-not-exist") is False


def test_save_rejects_path_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(chat, "SAVE_DIR", tmp_path)
    session = _session()

    assert session.save_conversation("../escape") is None
    assert session.load_conversation("../escape") is False
    # Nothing should have been written outside the save directory.
    assert not (tmp_path.parent / "escape.json").exists()
