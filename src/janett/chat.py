"""Core chat session and token counting functionality."""

import json
from datetime import datetime

import tiktoken
from openai import OpenAI
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
    get_openai_api_key,
)

console = Console()


class TokenCounter:
    """Count tokens for OpenAI models using tiktoken."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        try:
            self.encoding = tiktoken.get_encoding(model)
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

    def set_provider(self, provider: str, model: str | None = None):
        """Switch to a different provider."""
        self.provider = provider
        self.client = create_client(provider)
        if model:
            self.model = model

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
        """Change the model. Returns False if model is invalid."""
        if model not in MODELS:
            return False
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
        stream = self.client.chat.completions.create(
            model=self.model, stream=True, messages=self.messages
        )

        full_response = ""

        with Live(console=console, refresh_per_second=12, transient=False) as live:
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    full_response += token

                    # Minimal display - just markdown content
                    md = Markdown(full_response)
                    live.update(md)

        console.print()  # Add spacing after response
        out_tokens = self.token_counter.count(full_response)
        self.total_output_tokens += out_tokens
        self.add_assistant_message(full_response)
        return full_response

    def _get_response_sync(self) -> str:
        """Get response without streaming."""
        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages
        )

        full_response = response.choices[0].message.content or ""
        out_tokens = self.token_counter.count(full_response)
        self.total_output_tokens += out_tokens
        self.add_assistant_message(full_response)
        return full_response

    def get_token_stats(self) -> dict:
        """Get token usage statistics."""
        pricing = MODELS.get(self.model, MODELS[DEFAULT_MODEL])
        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]

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

    def save_conversation(self, filename: str) -> str:
        """Save conversation to a JSON file."""
        SAVE_DIR.mkdir(exist_ok=True)

        filepath = SAVE_DIR / filename
        if not filepath.suffix:
            filepath = filepath.with_suffix(".json")

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
        filepath = SAVE_DIR / filename
        if not filepath.suffix:
            filepath = filepath.with_suffix(".json")

        if not filepath.exists():
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
