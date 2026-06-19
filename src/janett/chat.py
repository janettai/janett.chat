"""Core chat session and token counting functionality."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import tiktoken
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from janett.config import (
    API_TIMEOUT,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_SYSTEM_PROMPT,
    PROVIDERS,
    SAVE_DIR,
    get_model_pricing,
    get_openai_api_key,
)

console = Console()


def stream_completion(
    client: OpenAI,
    model: str,
    messages: list[dict[str, str]],
    out_console: Console = console,
) -> str:
    """Stream a chat completion, rendering markdown live, and return the full text.

    Shared by chat mode, the chat UI, and the in-tutorial chat loop so the
    streaming/rendering logic lives in exactly one place.
    """
    stream = client.chat.completions.create(
        model=model,
        stream=True,
        messages=cast(list[ChatCompletionMessageParam], messages),
    )

    full_response = ""
    with Live(console=out_console, refresh_per_second=12, transient=False) as live:
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta is not None:
                full_response += delta
                live.update(Markdown(full_response))

    out_console.print()  # Add spacing after response
    return full_response


class TokenCounter:
    """Approximate token counts using tiktoken (calibrated for OpenAI models)."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        """Count tokens in a string."""
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict[str, str]]) -> int:
        """Count tokens in a list of messages."""
        total = 0
        for message in messages:
            total += 4
            total += self.count(message.get("content", ""))
            total += self.count(message.get("role", ""))
        total += 2
        return total


def create_client(provider: str = DEFAULT_PROVIDER) -> OpenAI:
    """Create an OpenAI client for the given provider."""
    provider_config = PROVIDERS.get(provider, PROVIDERS["ollama"])
    api_key = provider_config["api_key"]

    # For OpenAI, get API key from config/environment
    if provider == "openai":
        api_key = get_openai_api_key() or ""

    return OpenAI(
        base_url=provider_config["base_url"],
        api_key=api_key,
        timeout=API_TIMEOUT,
    )


class ChatSession:
    """Manage a chat session with LLM models."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        provider: str = DEFAULT_PROVIDER,
        client: OpenAI | None = None,
    ) -> None:
        self.model = model
        self.provider = provider
        self.system_prompt = system_prompt
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        self.token_counter = TokenCounter(model)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.client = client or create_client(provider)

    def set_provider(self, provider: str, model: str | None = None) -> None:
        """Switch to a different provider."""
        self.provider = provider
        self.client = create_client(provider)
        if model:
            self.model = model
            self.token_counter = TokenCounter(model)

    def add_user_msg(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation."""
        self.messages.append({"role": "assistant", "content": content})

    def clear_history(self) -> None:
        """Clear conversation history and reset token counts."""
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def set_system_prompt(self, prompt: str) -> None:
        """Set a new system prompt and clear history."""
        self.system_prompt = prompt
        self.clear_history()

    def set_model(self, model: str) -> bool:
        """Change the model and refresh the token counter.

        Any model name is accepted: Ollama models are discovered dynamically and
        are not known ahead of time. Returns True (kept for caller compatibility).
        """
        self.model = model
        self.token_counter = TokenCounter(model)
        return True

    def get_response(self, user_msg: str, stream: bool = True) -> str:
        """Get a response from the model."""
        from janett.ui import print_error

        self.add_user_msg(user_msg)

        input_tokens = self.token_counter.count_messages(self.messages)
        self.total_input_tokens += input_tokens

        try:
            if stream:
                return self._stream_response()
            else:
                return self._get_response_sync()

        except Exception as e:
            err_msg = str(e)
            self.messages.pop()
            print_error(f"API Error: {err_msg}")
            return ""

    def _stream_response(self) -> str:
        """Stream response with live updates - Claude Code style."""
        full_response = stream_completion(self.client, self.model, self.messages)
        out_tokens = self.token_counter.count(full_response)
        self.total_output_tokens += out_tokens
        self.add_assistant_message(full_response)
        return full_response

    def _get_response_sync(self) -> str:
        """Get response without streaming."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=cast(list[ChatCompletionMessageParam], self.messages),
        )

        full_response = response.choices[0].message.content or ""
        out_tokens = self.token_counter.count(full_response)
        self.total_output_tokens += out_tokens
        self.add_assistant_message(full_response)
        return full_response

    def get_token_stats(self) -> dict[str, Any]:
        """Get token usage statistics.

        Costs are only meaningful for OpenAI; local providers (Ollama) are free,
        so their dollar amounts are reported as zero rather than computed from a
        placeholder price table.
        """
        pricing = get_model_pricing(self.model)
        free = self.provider != "openai"
        input_cost = (
            0.0 if free else (self.total_input_tokens / 1_000_000) * pricing["input"]
        )
        output_cost = (
            0.0 if free else (self.total_output_tokens / 1_000_000) * pricing["output"]
        )

        return {
            "model": self.model,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "context_used": self.token_counter.count_messages(self.messages),
            "context_limit": pricing["context"],
        }

    def _resolve_save_path(self, filename: str) -> Path | None:
        """Resolve ``filename`` inside SAVE_DIR, or None if it escapes the dir."""
        candidate = SAVE_DIR / filename
        if not candidate.suffix:
            candidate = candidate.with_suffix(".json")

        save_root = SAVE_DIR.resolve()
        resolved = candidate.resolve()
        if resolved != save_root and save_root not in resolved.parents:
            return None
        return resolved

    def save_conversation(self, filename: str) -> str | None:
        """Save conversation to a JSON file.

        Returns the path written, or None if the filename escapes SAVE_DIR.
        """
        SAVE_DIR.mkdir(exist_ok=True)

        filepath = self._resolve_save_path(filename)
        if filepath is None:
            return None

        data = {
            "model": self.model,
            "system_prompt": self.system_prompt,
            "messages": self.messages[1:],
            "saved_at": datetime.now().isoformat(),
            "token_stats": {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def load_conversation(self, filename: str) -> bool:
        """Load conversation from a JSON file."""
        filepath = self._resolve_save_path(filename)
        if filepath is None or not filepath.exists():
            return False

        with open(filepath) as f:
            data = json.load(f)

        self.model = data.get("model", DEFAULT_MODEL)
        self.system_prompt = data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.messages.extend(data.get("messages", []))

        stats = data.get("token_stats", {})
        self.total_input_tokens = stats.get("input_tokens", 0)
        self.total_output_tokens = stats.get("output_tokens", 0)

        self.token_counter = TokenCounter(self.model)

        return True

    def get_message_count(self) -> int:
        """Get number of messages (excluding system)."""
        return len(self.messages) - 1
