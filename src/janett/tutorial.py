"""Tutorial session and data structures for Janett."""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from janett.chat import create_client
from janett.config import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    TUTORIAL_CONTINUE_PROMPT,
    TUTORIAL_SYSTEM_PROMPT,
)


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
    def from_json(cls, data: dict[str, Any]) -> "Tutorial":
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

    def get_chapter(self, index: int) -> Chapter | None:
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

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        provider: str = DEFAULT_PROVIDER,
        client: OpenAI | None = None,
    ) -> None:
        self.model = model
        self.provider = provider
        self.client = client or create_client(provider)
        self.tutorial: Tutorial | None = None
        self.current_chapter_index: int = 0
        self.last_raw_response: str = ""

    def set_provider(self, provider: str, model: str | None = None) -> None:
        """Switch to a different provider."""
        self.provider = provider
        self.client = create_client(provider)
        if model:
            self.model = model

    def generate_tutorial(self, topic: str) -> tuple[bool, str]:
        """Generate a tutorial for the given topic.

        Returns (success, error_message).
        """
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": TUTORIAL_SYSTEM_PROMPT},
            {"role": "user", "content": topic},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            content = response.choices[0].message.content or ""

            if not content:
                return False, "Empty response from model"

            tutorial_data = self._parse_response(content)
            if tutorial_data:
                self.tutorial = Tutorial.from_json(tutorial_data)
                self.current_chapter_index = 0
                return True, ""
            else:
                # Store raw response for debugging
                self.last_raw_response = content[:500]
                return False, "Could not parse tutorial structure from response"

        except Exception as e:
            return False, str(e)

    def _parse_response(self, response: str) -> dict[str, Any] | None:
        """Parse AI response to extract tutorial data from structured format."""
        response = response.strip()

        # Try to parse the structured text format
        result = self._parse_structured_format(response)
        if result:
            return result

        # Fallback: try JSON parsing for backwards compatibility
        return self._parse_json_format(response)

    def _parse_structured_format(self, response: str) -> dict[str, Any] | None:
        """Parse the ===TUTORIAL=== / ===CHAPTER=== format."""
        # Check if response has our markers
        if "===TUTORIAL===" not in response and "===CHAPTER" not in response:
            return None

        result: dict[str, Any] = {"title": "", "description": "", "chapters": []}

        # Extract tutorial title and description
        tutorial_match = re.search(
            r"===TUTORIAL===\s*\n\s*Title:\s*(.+?)\n\s*Description:\s*(.+?)(?=\n\s*===CHAPTER|\n\n)",
            response,
            re.DOTALL,
        )
        if tutorial_match:
            result["title"] = tutorial_match.group(1).strip()
            result["description"] = tutorial_match.group(2).strip()

        # Extract chapters
        chapter_pattern = r"===CHAPTER\s*(\d+)===\s*\nTitle:\s*(.+?)\nSummary:\s*(.+?)\n---\s*\n([\s\S]*?)(?=\n---|\n===CHAPTER|\n===END===|$)"
        chapters = re.findall(chapter_pattern, response)

        for chapter_num, title, summary, content in chapters:
            # Clean up content - remove trailing ---
            content = content.strip()
            if content.endswith("---"):
                content = content[:-3].strip()

            result["chapters"].append(
                {
                    "id": int(chapter_num),
                    "title": title.strip(),
                    "summary": summary.strip(),
                    "content": content,
                }
            )

        # If we found chapters, return the result
        if result["chapters"]:
            # Set default title if not found
            if not result["title"]:
                result["title"] = "Tutorial"
            return result

        return None

    def _parse_json_format(self, response: str) -> dict[str, Any] | None:
        """Fallback JSON parser for backwards compatibility."""
        # Try direct JSON parse
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "chapters" in data:
                return data
        except json.JSONDecodeError:
            pass

        # Try to find JSON in the response
        first_brace = response.find("{")
        last_brace = response.rfind("}")

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                json_str = response[first_brace : last_brace + 1]
                data = json.loads(json_str)
                if isinstance(data, dict) and "chapters" in data:
                    return data
            except json.JSONDecodeError:
                pass

        return None

    @property
    def current_chapter(self) -> Chapter | None:
        """Get the current chapter."""
        if self.tutorial:
            return self.tutorial.get_chapter(self.current_chapter_index)
        return None

    def next_chapter(self) -> bool:
        """Move to next chapter. Returns False if at end."""
        if (
            self.tutorial
            and self.current_chapter_index < self.tutorial.chapter_count - 1
        ):
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

    def generate_more_chapters(self, num_chapters: int = 3) -> tuple[bool, str]:
        """Generate additional chapters for the current tutorial.

        Returns (success, error_message).
        """
        if not self.tutorial:
            return False, "No tutorial loaded"

        # Build summary of completed chapters
        completed = "\n".join(
            f"- Chapter {ch.id}: {ch.title} - {ch.summary}"
            for ch in self.tutorial.chapters
        )

        start_num = self.tutorial.chapter_count + 1

        # Format the continuation prompt
        system_prompt = TUTORIAL_CONTINUE_PROMPT.format(
            completed_chapters=completed,
            num_chapters=num_chapters,
            start_num=start_num,
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Continue the tutorial on: {self.tutorial.title}",
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            content = response.choices[0].message.content or ""

            if not content:
                return False, "Empty response from model"

            # Parse new chapters
            new_chapters = self._parse_continuation(content, start_num)
            if new_chapters:
                # Add new chapters to existing tutorial
                self.tutorial.chapters.extend(new_chapters)
                # Move to first new chapter
                self.current_chapter_index = start_num - 1
                return True, ""
            else:
                self.last_raw_response = content[:500]
                return False, "Could not parse additional chapters"

        except Exception as e:
            return False, str(e)

    def _parse_continuation(self, response: str, start_num: int) -> list[Chapter]:
        """Parse continuation response to extract new chapters."""
        chapters: list[Chapter] = []

        # Extract chapters using the same pattern
        chapter_pattern = r"===CHAPTER\s*(\d+)===\s*\nTitle:\s*(.+?)\nSummary:\s*(.+?)\n---\s*\n([\s\S]*?)(?=\n---|\n===CHAPTER|\n===END===|$)"
        matches = re.findall(chapter_pattern, response)

        for chapter_num, title, summary, content in matches:
            content = content.strip()
            if content.endswith("---"):
                content = content[:-3].strip()

            chapters.append(
                Chapter(
                    id=int(chapter_num),
                    title=title.strip(),
                    summary=summary.strip(),
                    content=content,
                )
            )

        return chapters

    def reset(self) -> None:
        """Reset the tutorial session."""
        self.tutorial = None
        self.current_chapter_index = 0
