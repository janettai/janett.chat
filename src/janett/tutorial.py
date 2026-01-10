"""Tutorial session and data structures for Janett."""

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

from janett.config import DEFAULT_MODEL, TUTORIAL_SYSTEM_PROMPT


@dataclass
class Chapter:
    """Represents a single chapter in a tutorial."""

    id: int
    title: str
    summary: str
    content: str


@dataclass
class Tutorial:
    """Represents a complete tutorial with chapters."""

    title: str
    description: str
    chapters: list[Chapter] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "Tutorial":
        """Create Tutorial from parsed JSON response."""
        chapters = [
            Chapter(
                id=ch.get("id", i + 1),
                title=ch.get("title", f"Chapter {i + 1}"),
                summary=ch.get("summary", ""),
                content=ch.get("content", ""),
            )
            for i, ch in enumerate(data.get("chapters", []))
        ]
        return cls(
            title=data.get("title", "Untitled Tutorial"),
            description=data.get("description", ""),
            chapters=chapters,
        )

    def get_chapter(self, index: int) -> Optional[Chapter]:
        """Get chapter by 0-based index."""
        if 0 <= index < len(self.chapters):
            return self.chapters[index]
        return None

    @property
    def chapter_count(self) -> int:
        """Return total number of chapters."""
        return len(self.chapters)


class TutorialSession:
    """Manages a tutorial session with chapter navigation."""

    def __init__(self, model: str = DEFAULT_MODEL, client: OpenAI | None = None):
        self.model = model
        self.client = client or OpenAI()
        self.tutorial: Optional[Tutorial] = None
        self.current_chapter_index: int = 0

    def generate_tutorial(self, topic: str) -> bool:
        """Generate a tutorial for the given topic.

        Returns True if successful, False otherwise.
        """
        messages = [
            {"role": "system", "content": TUTORIAL_SYSTEM_PROMPT},
            {"role": "user", "content": topic},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            content = response.choices[0].message.content or ""

            tutorial_data = self._parse_response(content)
            if tutorial_data:
                self.tutorial = Tutorial.from_json(tutorial_data)
                self.current_chapter_index = 0
                return True
        except Exception:
            pass

        return False

    def _parse_response(self, response: str) -> Optional[dict]:
        """Parse AI response to extract JSON tutorial data."""
        # Try direct JSON parse first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
        match = re.search(json_pattern, response)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object in response
        brace_pattern = r"\{[\s\S]*\"chapters\"[\s\S]*\}"
        match = re.search(brace_pattern, response)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    @property
    def current_chapter(self) -> Optional[Chapter]:
        """Get the current chapter."""
        if self.tutorial:
            return self.tutorial.get_chapter(self.current_chapter_index)
        return None

    def next_chapter(self) -> bool:
        """Move to next chapter. Returns False if at end."""
        if self.tutorial and self.current_chapter_index < self.tutorial.chapter_count - 1:
            self.current_chapter_index += 1
            return True
        return False

    def prev_chapter(self) -> bool:
        """Move to previous chapter. Returns False if at start."""
        if self.tutorial and self.current_chapter_index > 0:
            self.current_chapter_index -= 1
            return True
        return False

    def go_to_chapter(self, index: int) -> bool:
        """Jump to a specific chapter by 0-based index."""
        if self.tutorial and 0 <= index < self.tutorial.chapter_count:
            self.current_chapter_index = index
            return True
        return False

    def has_tutorial(self) -> bool:
        """Check if a tutorial is loaded."""
        return self.tutorial is not None

    def reset(self):
        """Reset the tutorial session."""
        self.tutorial = None
        self.current_chapter_index = 0
