import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI

import tiktoken
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.rule import Rule
from rich.status import Status
from rich.align import Align
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

client = OpenAI()
console = Console()

# Theme colors
THEME = {
    "primary": "#7C3AED",      # Violet
    "secondary": "#06B6D4",    # Cyan
    "success": "#10B981",      # Emerald
    "warning": "#F59E0B",      # Amber
    "error": "#EF4444",        # Red
    "muted": "#6B7280",        # Gray
    "user": "#3B82F6",         # Blue
    "assistant": "#8B5CF6",    # Purple
}

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

SAVE_DIR = Path("./conversations")

APP_NAME = "Janett"
VERSION = "1.0.0"


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
        total += 2
        return total


class ChatSession:
    def __init__(
        self, model: str = DEFAULT_MODEL, system_prompt: str = DEFAULT_SYSTEM_PROMPT
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
        self.messages.append({"role": "assistant", "content": content})

    def clear_history(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.total_input_tokens = 0
        self.total_output_tokens = 0

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

            with Live(console=console, refresh_per_second=12, transient=False) as live:
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        token = chunk.choices[0].delta.content
                        full_response += token

                        md = Markdown(full_response)
                        panel = Panel(
                            md,
                            title=f"[bold {THEME['assistant']}]Assistant[/]",
                            title_align="left",
                            border_style=Style(color=THEME["assistant"]),
                            padding=(1, 2),
                            subtitle=f"[dim]{self.model}[/]",
                            subtitle_align="right",
                        )
                        live.update(panel)

            out_tokens = self.token_counter.count(full_response)
            self.total_output_tokens += out_tokens
            self.add_assistant_message(full_response)
            return full_response

        except Exception as e:
            err_msg = str(e)
            self.messages.pop()
            print_error(f"API Error: {err_msg}")
            return ""

    def get_token_stats(self) -> Dict:
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
        filepath = SAVE_DIR / filename
        if not filepath.suffix:
            filepath = filepath.with_suffix(".json")

        if not filepath.exists():
            return False

        with open(filepath, "r") as f:
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
        return len(self.messages) - 1


def print_header():
    """Print the application header with branding."""
    console.print()

    logo = Text()
    logo.append("  ╭─────────────────────────────╮\n", style=THEME["primary"])
    logo.append("  │", style=THEME["primary"])
    logo.append(f"  {APP_NAME}", style=f"bold {THEME['primary']}")
    logo.append(" Chat", style=f"{THEME['muted']}")
    logo.append("              │\n", style=THEME["primary"])
    logo.append("  │", style=THEME["primary"])
    logo.append("  Your AI conversation partner", style=f"dim {THEME['muted']}")
    logo.append(" │\n", style=THEME["primary"])
    logo.append("  ╰─────────────────────────────╯", style=THEME["primary"])

    console.print(logo)
    console.print()


def print_welcome(model: str):
    """Print welcome message with current session info."""
    info = Table.grid(padding=(0, 2))
    info.add_column(style=f"dim {THEME['muted']}")
    info.add_column(style="dim")

    info.add_row("Model", f"[bold]{model}[/]")
    info.add_row("Commands", "[dim]/help[/]")

    panel = Panel(
        info,
        title=f"[{THEME['success']}]Session Started[/]",
        title_align="left",
        border_style=Style(color=THEME["success"], dim=True),
        padding=(0, 2),
    )
    console.print(panel)


def print_help():
    """Print help information with improved styling."""
    console.print()

    table = Table(
        show_header=True,
        header_style=f"bold {THEME['primary']}",
        border_style=THEME["muted"],
        title=f"[bold {THEME['primary']}]Available Commands[/]",
        title_justify="left",
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Command", style=f"bold {THEME['secondary']}", no_wrap=True)
    table.add_column("Description", style="dim")

    commands = [
        ("/help", "Show this help message"),
        ("/clear", "Clear conversation history"),
        ("/save <name>", "Save conversation to file"),
        ("/load <name>", "Load conversation from file"),
        ("/list", "List saved conversations"),
        ("/system", "Set a new system prompt"),
        ("/model", "Change the AI model"),
        ("/tokens", "Show token usage and cost"),
        ("/quit", "Exit the chat"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)
    console.print()


def print_token_stats(stats: dict):
    """Print token usage statistics with improved styling."""
    console.print()

    # Create main stats table
    table = Table(
        show_header=False,
        border_style=THEME["muted"],
        padding=(0, 2),
        expand=False,
    )
    table.add_column("Metric", style=f"{THEME['muted']}")
    table.add_column("Value", justify="right", style="bold")

    # Token section
    table.add_row("Input Tokens", f"{stats['input_tokens']:,}")
    table.add_row("Output Tokens", f"{stats['output_tokens']:,}")
    table.add_row(
        Text("Total Tokens", style=f"bold {THEME['primary']}"),
        Text(f"{stats['total_tokens']:,}", style=f"bold {THEME['primary']}")
    )
    table.add_row("", "")

    # Cost section
    table.add_row("Input Cost", f"${stats['input_cost']:.4f}")
    table.add_row("Output Cost", f"${stats['output_cost']:.4f}")
    table.add_row(
        Text("Total Cost", style=f"bold {THEME['success']}"),
        Text(f"${stats['total_cost']:.4f}", style=f"bold {THEME['success']}")
    )
    table.add_row("", "")

    # Context section
    context_pct = (stats['context_used'] / stats['context_limit']) * 100
    context_style = THEME['success'] if context_pct < 50 else (THEME['warning'] if context_pct < 80 else THEME['error'])
    table.add_row(
        "Context Usage",
        Text(f"{stats['context_used']:,} / {stats['context_limit']:,} ({context_pct:.1f}%)", style=context_style)
    )

    panel = Panel(
        table,
        title=f"[bold {THEME['secondary']}]Token Usage[/] [dim]({stats['model']})[/]",
        title_align="left",
        border_style=Style(color=THEME["secondary"], dim=True),
        padding=(1, 1),
    )
    console.print(panel)
    console.print()


def print_models(current_model: str):
    """Print available models with improved styling."""
    console.print()

    table = Table(
        show_header=True,
        header_style=f"bold {THEME['primary']}",
        border_style=THEME["muted"],
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Model", style=f"{THEME['secondary']}")
    table.add_column("Input", justify="right", style="dim")
    table.add_column("Output", justify="right", style="dim")
    table.add_column("Context", justify="right", style="dim")
    table.add_column("", style="dim")

    for model, info in MODELS.items():
        indicator = f"[bold {THEME['success']}]<--[/]" if model == current_model else ""
        model_style = f"bold {THEME['secondary']}" if model == current_model else THEME['secondary']
        table.add_row(
            Text(model, style=model_style),
            f"${info['input']:.2f}",
            f"${info['output']:.2f}",
            f"{info['context']:,}",
            indicator,
        )

    panel = Panel(
        table,
        title=f"[bold {THEME['primary']}]Available Models[/] [dim](per 1M tokens)[/]",
        title_align="left",
        border_style=Style(color=THEME["primary"], dim=True),
        padding=(0, 1),
    )
    console.print(panel)
    console.print()


def list_saved_conversations():
    """List saved conversation files with improved styling."""
    console.print()

    if not SAVE_DIR.exists():
        print_info("No saved conversations found.")
        return

    files = list(SAVE_DIR.glob("*.json"))
    if not files:
        print_info("No saved conversations found.")
        return

    table = Table(
        show_header=True,
        header_style=f"bold {THEME['primary']}",
        border_style=THEME["muted"],
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Name", style=f"bold {THEME['secondary']}")
    table.add_column("Saved", style="dim")
    table.add_column("Messages", justify="right")
    table.add_column("Model", style="dim")

    for filepath in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(filepath) as f:
                data = json.load(f)
            saved_at = data.get("saved_at", "")[:16].replace("T", " ")
            msg_count = len(data.get("messages", []))
            model = data.get("model", "unknown")
            table.add_row(filepath.stem, saved_at, str(msg_count), model)
        except Exception:
            table.add_row(filepath.stem, "[red]Error[/]", "-", "-")

    panel = Panel(
        table,
        title=f"[bold {THEME['primary']}]Saved Conversations[/]",
        title_align="left",
        border_style=Style(color=THEME["primary"], dim=True),
        padding=(0, 1),
    )
    console.print(panel)
    console.print()


def print_user_message(content: str):
    """Display user message with styling."""
    console.print()
    panel = Panel(
        content,
        title=f"[bold {THEME['user']}]You[/]",
        title_align="left",
        border_style=Style(color=THEME["user"]),
        padding=(0, 2),
    )
    console.print(panel)


def print_success(message: str):
    """Print success message."""
    console.print(f"[{THEME['success']}]✓[/] {message}")


def print_error(message: str):
    """Print error message with panel."""
    console.print()
    panel = Panel(
        f"[{THEME['error']}]{message}[/]",
        title=f"[bold {THEME['error']}]Error[/]",
        title_align="left",
        border_style=Style(color=THEME["error"]),
        padding=(0, 2),
    )
    console.print(panel)
    console.print()


def print_info(message: str):
    """Print info message."""
    console.print(f"[{THEME['muted']}]{message}[/]")


def print_divider():
    """Print a subtle divider."""
    console.print(Rule(style=f"dim {THEME['muted']}"))


def get_prompt() -> str:
    """Get styled input prompt."""
    return f"[bold {THEME['user']}]>[/] "


def print_goodbye(stats: dict):
    """Print goodbye message with session summary."""
    console.print()

    if stats["total_tokens"] > 0:
        summary = Text()
        summary.append("Session Summary\n", style=f"bold {THEME['primary']}")
        summary.append(f"Messages: {stats.get('messages', 0)}  ", style="dim")
        summary.append(f"Tokens: {stats['total_tokens']:,}  ", style="dim")
        summary.append(f"Cost: ${stats['total_cost']:.4f}", style="dim")

        panel = Panel(
            summary,
            border_style=Style(color=THEME["muted"], dim=True),
            padding=(0, 2),
        )
        console.print(panel)

    console.print()
    console.print(f"[{THEME['warning']}]Goodbye! Thanks for chatting.[/]")
    console.print()


def main():
    session = ChatSession()

    print_header()
    print_welcome(session.model)

    while True:
        try:
            console.print()
            user_input = Prompt.ask(get_prompt())
            user_input = user_input.strip()

        except (KeyboardInterrupt, EOFError):
            stats = session.get_token_stats()
            stats["messages"] = session.get_message_count()
            print_goodbye(stats)
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
                stats["messages"] = session.get_message_count()
                print_goodbye(stats)
                break

            elif command == "/help":
                print_help()

            elif command == "/clear":
                console.print()
                if Confirm.ask(
                    f"[{THEME['warning']}]Clear conversation history?[/]",
                    default=False
                ):
                    session.clear_history()
                    print_success("Conversation cleared.")
                else:
                    print_info("Cancelled.")

            elif command == "/tokens":
                stats = session.get_token_stats()
                print_token_stats(stats)

            elif command == "/model":
                print_models(session.model)
                new_model = Prompt.ask(
                    f"[{THEME['muted']}]Enter model name[/]",
                    default=session.model
                )
                if session.set_model(new_model):
                    print_success(f"Model changed to {new_model}")
                else:
                    print_error(f"Unknown model: {new_model}")

            elif command == "/system":
                console.print()
                console.print(f"[{THEME['muted']}]Enter new system prompt (or 'cancel'):[/]")
                new_prompt = Prompt.ask(f"[dim]Prompt[/]")
                if new_prompt.lower() != "cancel" and new_prompt:
                    session.set_system_prompt(new_prompt)
                    print_success("System prompt updated.")
                else:
                    print_info("Cancelled.")

            elif command == "/save":
                if not args:
                    args = Prompt.ask(
                        f"[{THEME['muted']}]Filename[/]",
                        default="conversation"
                    )
                filepath = session.save_conversation(args)
                print_success(f"Saved to {filepath}")

            elif command == "/load":
                if not args:
                    list_saved_conversations()
                    args = Prompt.ask(f"[{THEME['muted']}]Filename[/]")
                if session.load_conversation(args):
                    print_success(f"Loaded: {args}")
                    print_info(f"Model: {session.model} | Messages: {session.get_message_count()}")
                else:
                    print_error(f"Could not load: {args}")

            elif command == "/list":
                list_saved_conversations()

            else:
                print_error(f"Unknown command: {command}")
                print_info("Type /help for available commands.")

            continue

        # Display user message
        print_user_message(user_input)

        # Get response with loading indicator
        console.print()
        with console.status(
            f"[{THEME['muted']}]Thinking...[/]",
            spinner="dots",
            spinner_style=THEME["assistant"]
        ):
            pass  # Status shows briefly before streaming begins

        session.get_response(user_input)


if __name__ == "__main__":
    main()
