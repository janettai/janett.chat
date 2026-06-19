"""Tests for tutorial parsing and chapter navigation."""

import json

from janett.tutorial import Chapter, Tutorial, TutorialSession

from .conftest import SAMPLE_CONTINUATION, SAMPLE_TUTORIAL, FakeClient


def _session() -> TutorialSession:
    """A session wired to a fake client so no network call happens."""
    return TutorialSession(client=FakeClient(SAMPLE_TUTORIAL))  # type: ignore[arg-type]


def test_parse_structured_format_extracts_chapters() -> None:
    session = _session()
    data = session._parse_structured_format(SAMPLE_TUTORIAL)

    assert data is not None
    assert data["title"] == "Test Tutorial"
    assert data["description"] == "A short description"
    assert len(data["chapters"]) == 2
    assert data["chapters"][0]["id"] == 1
    assert data["chapters"][0]["title"] == "Intro"
    # Trailing --- markers should be stripped from content.
    assert data["chapters"][0]["content"] == "Content one."
    assert "---" not in data["chapters"][1]["content"]


def test_parse_structured_format_returns_none_without_markers() -> None:
    session = _session()
    assert session._parse_structured_format("just some prose") is None


def test_parse_json_format_fallback() -> None:
    session = _session()
    payload = json.dumps(
        {
            "title": "JSON Tut",
            "description": "via json",
            "chapters": [{"id": 1, "title": "A", "summary": "s", "content": "c"}],
        }
    )
    data = session._parse_json_format(payload)
    assert data is not None
    assert data["title"] == "JSON Tut"


def test_parse_json_format_embedded_in_text() -> None:
    session = _session()
    payload = 'noise before {"chapters": [{"title": "A"}]} noise after'
    data = session._parse_json_format(payload)
    assert data is not None
    assert "chapters" in data


def test_parse_json_format_rejects_non_dict() -> None:
    session = _session()
    assert session._parse_json_format("[1, 2, 3]") is None


def test_parse_continuation_numbers_from_start() -> None:
    session = _session()
    chapters = session._parse_continuation(SAMPLE_CONTINUATION, start_num=3)
    assert len(chapters) == 1
    assert chapters[0].id == 3
    assert chapters[0].title == "Advanced"
    assert chapters[0].content == "Content three."


def test_generate_tutorial_with_fake_client() -> None:
    session = _session()
    ok, error = session.generate_tutorial("anything")

    assert ok is True
    assert error == ""
    assert session.tutorial is not None
    assert session.tutorial.chapter_count == 2
    assert session.current_chapter_index == 0


def test_generate_tutorial_parse_failure() -> None:
    session = TutorialSession(client=FakeClient("no markers here"))  # type: ignore[arg-type]
    ok, error = session.generate_tutorial("anything")
    assert ok is False
    assert error
    assert session.tutorial is None


def test_generate_more_chapters_appends() -> None:
    session = _session()
    session.generate_tutorial("anything")
    # Swap the fake's payload to the continuation text for the next call.
    session.client = FakeClient(SAMPLE_CONTINUATION)  # type: ignore[assignment]

    ok, error = session.generate_more_chapters(1)
    assert ok is True, error
    assert session.tutorial is not None
    assert session.tutorial.chapter_count == 3
    # Jumps to the first new chapter (0-based index 2).
    assert session.current_chapter_index == 2


def _navigable_session() -> TutorialSession:
    session = _session()
    session.tutorial = Tutorial(
        title="t",
        description="d",
        chapters=[
            Chapter(id=1, title="A", summary="", content=""),
            Chapter(id=2, title="B", summary="", content=""),
            Chapter(id=3, title="C", summary="", content=""),
        ],
    )
    return session


def test_navigation_bounds() -> None:
    session = _navigable_session()

    assert session.has_tutorial() is True
    assert session.prev_chapter() is False  # already at first
    assert session.next_chapter() is True
    assert session.current_chapter_index == 1
    assert session.go_to_chapter(2) is True
    assert session.next_chapter() is False  # already at last
    assert session.go_to_chapter(99) is False
    assert session.go_to_chapter(-1) is False


def test_reset_clears_state() -> None:
    session = _navigable_session()
    session.current_chapter_index = 2
    session.reset()
    assert session.tutorial is None
    assert session.current_chapter_index == 0
    assert session.has_tutorial() is False
