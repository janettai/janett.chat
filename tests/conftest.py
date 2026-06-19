"""Shared test fixtures and fakes.

These tests never touch the network: an in-memory fake stands in for the
OpenAI client (which ``ChatSession``/``TutorialSession`` accept via their
``client=`` constructor argument).
"""

from types import SimpleNamespace
from typing import Any


def _make_response(content: str) -> SimpleNamespace:
    """Build an object shaped like an OpenAI ChatCompletion response."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


class FakeClient:
    """Minimal stand-in for ``openai.OpenAI`` returning canned content."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return _make_response(self.content)


SAMPLE_TUTORIAL = """===TUTORIAL===
Title: Test Tutorial
Description: A short description

===CHAPTER 1===
Title: Intro
Summary: First chapter
---
Content one.
---

===CHAPTER 2===
Title: Deep Dive
Summary: Second chapter
---
Content two.
---

===END===
"""

SAMPLE_CONTINUATION = """===CHAPTER 3===
Title: Advanced
Summary: Third chapter
---
Content three.
---

===END===
"""
