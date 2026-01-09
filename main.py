import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI

import tiktoken
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.table import Table
from rich.text import Text

load_dotenv()

client = OpenAI()
console = Console()

MODELS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "context": 128000},
    "gpt-4o": {"input": 5.00, "output": 15.00, "context": 128000},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00, "context": 128000},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50, "context": 16385},
}

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_SYSTEM_PROMPT = """You are a helpful, knowledgeable assistant.
When providing code examples, use proper markdown code blocks with language specification.
Be concise but thorough. If you're unsure about something, say so."""

# Directory for saved conversations
SAVE_DIR = Path("./conversations")

MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = """You are a helpful assistant. 
You can remember the contexrt of our conversation
and can reference previous messages. Be concise in your responses."""


class TokenCounter:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        try:
            self.encoding = tiktoken.get_encoding(model)
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict[str, str]]) -> int:
        total = 0
        for message in messages:
            total += 4
            total += self.count(message.get("content", ""))
            total += self.count(message.get("role", ""))
        total += 2  # reply priming
        return total


class ChatSession:
    def __init__(
        self, model: str = DEFAULT_MODEL, system_prompt: str = SYSTEM_PROMPT
    ) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        self.token_counter = TokenCounter(model)
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def add_user_msg(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "system", "content": content})

    def clear_history(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt
        self.clear_history()

    def set_model(self, model: str) -> bool:
        if model not in MODELS:
            return False

        self.model = model
        self.token_counter = TokenCounter(model)
        return True

    def get_response(self, user_msg: str) -> str:
        self.add_user_msg(user_msg)

        input_tokens = self.token_counter.count_messages(self.messages)
        self.total_input_tokens += input_tokens
        try:
            stream = client.chat.completions.create(
                model=self.model, stream=True, messages=self.messages
            )

            full_response = ""

            with Live(console=console, refresh_per_second=10) as live:
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        token = chunk.choices[0].delta.content
                        full_response += token

                        # print token immediately
                        md = Markdown(full_response)
                        panel = Panel(
                            md,
                            title="[bold blue]Assistant[/bold blue]",
                            border_style="blue",
                            padding=(1, 2),
                        )
                        live.update(panel)

            out_tokens = self.token_counter.count(full_response)
            self.total_output_tokens += out_tokens
            self.add_assistant_message(full_response)
            return full_response
        except Exception as e:
            err_msg = f"Error: {e}"
            self.messages.pop()
            console.print(f"[red]{error_msg}[/red]")
            return err_msg

    def get_token_stats(self) -> Dict:
        pricing = MODELS.get(self.model, MODELS[DEFAULT_MODEL])

        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]

        return {
            "model": self.model,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "context_used": self.token_counter.count_messages(self.messages),
            "context_limit": pricing["context"],
        }

    def save_conversation(self, filename: str) -> str:
        SAVE_DIR.mkdir(exist_ok=True)

        filepath = SAVE_DIR / filename
        if not filepath.suffix:
            filepath = filepath.with_suffix(".json")

        data = {
            "model": self.model,
            "system_prompt": self.system_prompt,
            "messages": self.messages[1:],  # Exclude system message
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

        with open(filepath, "r") as f:
            data = json.load(f)

        # Restore state
        self.model = data.get("model", DEFAULT_MODEL)
        self.system_prompt = data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.messages.extend(data.get("messages", []))

        # Restore token counts if available
        stats = data.get("token_stats", {})
        self.total_input_tokens = stats.get("input_tokens", 0)
        self.total_output_tokens = stats.get("output_tokens", 0)

        self.token_counter = TokenCounter(self.model)

        return True

    def get_message_count(self) -> int:
        """Get number of messages (excluding system)."""
        return len(self.messages) - 1


def print_header(model: str):
    """Print the application header."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]OpenAI Terminal Chat[/bold cyan]\n"
            f"[dim]Model: {model}[/dim]\n"
            "[dim]Type /help for commands[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def print_help():
    """Print help information."""
    table = Table(title="Available Commands", border_style="green")
    table.add_column("Command", style="cyan")
    table.add_column("Description")

    commands = [
        ("/help", "Show this help message"),
        ("/clear", "Clear conversation history"),
        ("/save <name>", "Save conversation to file"),
        ("/load <name>", "Load conversation from file"),
        ("/list", "List saved conversations"),
        ("/system", "Set a new system prompt"),
        ("/model", "Change the model"),
        ("/tokens", "Show token usage and cost"),
        ("/quit", "Exit the chat"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)


def print_token_stats(stats: dict):
    table = Table(title="Token Usage", border_style="blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Model", stats["model"])
    table.add_row("Input Tokens", f"{stats.get('input_tokens', 0):,}")
    table.add_row("Output Tokens", f"{stats.get('output_tokens', 0):,}")
    table.add_row("Total Tokens", f"{stats.get('total_tokens', 0):,}")
    table.add_row("", "")
    table.add_row("Input Cost", f"${stats.get('input_cost', 0):.6f}")
    table.add_row("Output Cost", f"${stats.get('output_cost', 0):.6f}")
    table.add_row(
        "[bold]Total Cost[/bold]", f"[bold]${stats.get('total_cost', 0):.6f}[/bold]"
    )
    table.add_row("", "")
    table.add_row(
        "Context Used",
        f"{stats.get('context_used', 0):,} / {stats.get('context_limit', 0):,}",
    )

    console.print(table)


def print_models():
    """Print available models."""
    table = Table(title="Available Models", border_style="cyan")
    table.add_column("Model", style="cyan")
    table.add_column("Input $/1M", justify="right")
    table.add_column("Output $/1M", justify="right")
    table.add_column("Context", justify="right")

    for model, info in MODELS.items():
        table.add_row(
            model,
            f"${info['input']:.2f}",
            f"${info['output']:.2f}",
            f"{info['context']:,}",
        )

    console.print(table)


def list_saved_conversations():
    """List saved conversation files."""
    if not SAVE_DIR.exists():
        console.print("[yellow]No saved conversations found.[/yellow]")
        return

    files = list(SAVE_DIR.glob("*.json"))
    if not files:
        console.print("[yellow]No saved conversations found.[/yellow]")
        return

    table = Table(title="Saved Conversations", border_style="green")
    table.add_column("Filename", style="cyan")
    table.add_column("Saved At")
    table.add_column("Messages", justify="right")

    for filepath in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(filepath) as f:
                data = json.load(f)
            saved_at = data.get("saved_at", "Unknown")[:19]
            msg_count = len(data.get("messages", []))
            table.add_row(filepath.stem, saved_at, str(msg_count))
        except Exception:
            table.add_row(filepath.stem, "Error reading", "-")

    console.print(table)


def main():
    session = ChatSession()
    print_header(session.model)

    while True:
        try:
            console.print()
            user_input = Prompt.ask("[bold green]You[/bold green]")
            user_input = user_input.strip()

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if command in ("/quit", "/exit", "/q"):
                stats = session.get_token_stats()
                if stats["total_tokens"] > 0:
                    console.print()
                    print_token_stats(stats)
                console.print("\n[yellow]Goodbye![/yellow]")
                break

            elif command == "/help":
                print_help()

            elif command == "/clear":
                if Confirm.ask("Clear conversation history?", default=False):
                    session.clear_history()
                    console.print("[green]History cleared.[/green]")

            elif command == "/tokens":
                stats = session.get_token_stats()
                print_token_stats(stats)

            elif command == "/model":
                print_models()
                console.print()
                new_model = Prompt.ask("Enter model name", default=session.model)
                if session.set_model(new_model):
                    console.print(f"[green]Model changed to {new_model}[/green]")
                else:
                    console.print(f"[red]Unknown model: {new_model}[/red]")

            elif command == "/system":
                console.print("Enter new system prompt (or 'cancel'):")
                new_prompt = Prompt.ask("[dim]Prompt[/dim]")
                if new_prompt.lower() != "cancel" and new_prompt:
                    session.set_system_prompt(new_prompt)
                    console.print("[green]System prompt updated.[/green]")

            elif command == "/save":
                if not args:
                    args = Prompt.ask("Filename", default="conversation")
                filepath = session.save_conversation(args)
                console.print(f"[green]Saved to {filepath}[/green]")

            elif command == "/load":
                if not args:
                    list_saved_conversations()
                    args = Prompt.ask("Filename")
                if session.load_conversation(args):
                    console.print(f"[green]Loaded {args}[/green]")
                    console.print(
                        f"[dim]Model: {session.model}, Messages: {session.get_message_count()}[/dim]"
                    )
                else:
                    console.print(f"[red]Could not load: {args}[/red]")

            elif command == "/list":
                list_saved_conversations()

            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                print_help()

            continue

        # Display user message
        console.print()
        console.print(
            Panel(
                user_input,
                title="[bold green]You[/bold green]",
                border_style="green",
                padding=(0, 2),
            )
        )

        # Get response
        console.print()
        session.get_response(user_input)


if __name__ == "__main__":
    main()
