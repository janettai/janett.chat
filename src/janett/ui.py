"""Terminal UI components for Janett."""

import json
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from janett.config import (
    OPENAI_MODELS,
    PROVIDERS,
    SAVE_DIR,
    THEME,
    get_ollama_models,
)
from janett.tutorial import Chapter, Tutorial

console = Console()


def print_help() -> None:
    """Print help information with minimal styling."""
    console.print()
    console.print("[bold]Commands[/]")
    console.print()

    commands = [
        ("/help", "Show this help message"),
        ("/clear", "Clear conversation history"),
        ("/save <name>", "Save conversation to file"),
        ("/load <name>", "Load conversation from file"),
        ("/list", "List saved conversations"),
        ("/system", "Set a new system prompt"),
        ("/model", "Change the AI model"),
        ("/tokens", "Show token usage and cost"),
        ("/refresh", "Refresh the screen"),
        ("/quit", "Exit the chat"),
    ]

    for cmd, desc in commands:
        console.print(f"  [bold {THEME['primary']}]{cmd:<15}[/] [dim]{desc}[/]")

    console.print()


def print_token_stats(stats: dict[str, Any]) -> None:
    """Print token usage statistics with minimal styling."""
    console.print()
    console.print(f"[bold]Token Usage[/] [dim]({stats['model']})[/]")
    console.print()

    console.print(
        f"  [dim]Input[/]    {stats['input_tokens']:,} tokens  "
        f"[dim](${stats['input_cost']:.4f})[/]"
    )
    console.print(
        f"  [dim]Output[/]   {stats['output_tokens']:,} tokens  "
        f"[dim](${stats['output_cost']:.4f})[/]"
    )
    console.print(
        f"  [bold]Total[/]    {stats['total_tokens']:,} tokens  "
        f"[bold {THEME['success']}](${stats['total_cost']:.4f})[/]"
    )

    context_pct = (stats["context_used"] / stats["context_limit"]) * 100
    context_style = (
        THEME["success"]
        if context_pct < 50
        else (THEME["warning"] if context_pct < 80 else THEME["error"])
    )
    console.print()
    console.print(
        f"  [dim]Context[/]  [{context_style}]{stats['context_used']:,} / "
        f"{stats['context_limit']:,} ({context_pct:.1f}%)[/]"
    )
    console.print()


def print_models(current_model: str, provider: str = "ollama") -> None:
    """Print available models for the current provider."""
    console.print()

    if provider == "ollama":
        models = get_ollama_models()
        if not models:
            console.print("[bold]Models[/] [dim](Ollama)[/]")
            console.print()
            console.print(f"  [{THEME['error']}]No models found. Is Ollama running?[/]")
            console.print("  [dim]Run: ollama pull llama3.2[/]")
        else:
            console.print("[bold]Models[/] [dim](Ollama - Local)[/]")
            console.print()
            for model in models:
                if model == current_model:
                    console.print(
                        f"  [bold {THEME['primary']}]{model}[/] "
                        f"[bold {THEME['success']}]*[/]"
                    )
                else:
                    console.print(f"  [dim]{model}[/]")
    else:
        console.print("[bold]Models[/] [dim](OpenAI - per 1M tokens)[/]")
        console.print()
        for model, info in OPENAI_MODELS.items():
            if model == current_model:
                console.print(
                    f"  [bold {THEME['primary']}]{model}[/] "
                    f"[dim]in:${info['input']:.2f} out:${info['output']:.2f}[/] "
                    f"[bold {THEME['success']}]*[/]"
                )
            else:
                console.print(
                    f"  [dim]{model}[/] "
                    f"[dim]in:${info['input']:.2f} out:${info['output']:.2f}[/]"
                )

    console.print()


def print_providers(current_provider: str) -> None:
    """Print available providers."""
    console.print()
    console.print("[bold]Providers[/]")
    console.print()

    for key, info in PROVIDERS.items():
        if key == current_provider:
            console.print(
                f"  [bold {THEME['primary']}]{key}[/] [dim]{info['name']}[/] "
                f"[bold {THEME['success']}]*[/]"
            )
        else:
            console.print(f"  [dim]{key}[/] [dim]{info['name']}[/]")

    console.print()


def list_saved_conversations() -> None:
    """List saved conversation files with minimal styling."""
    console.print()

    if not SAVE_DIR.exists():
        print_info("No saved conversations found.")
        return

    files = list(SAVE_DIR.glob("*.json"))
    if not files:
        print_info("No saved conversations found.")
        return

    console.print("[bold]Saved Conversations[/]")
    console.print()

    for filepath in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(filepath) as f:
                data = json.load(f)
            saved_at = data.get("saved_at", "")[:16].replace("T", " ")
            msg_count = len(data.get("messages", []))
            model = data.get("model", "unknown")
            console.print(
                f"  [bold]{filepath.stem}[/] "
                f"[dim]{saved_at} • {msg_count} msgs • {model}[/]"
            )
        except Exception:
            console.print(f"  [bold]{filepath.stem}[/] [red]Error loading[/]")

    console.print()


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[{THEME['success']}]✓[/] {message}")


def print_error(message: str) -> None:
    """Print error message with minimal styling."""
    console.print()
    console.print(f"[{THEME['error']}]Error:[/] {message}")
    console.print()


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[{THEME['muted']}]{message}[/]")


def print_tutorial_help() -> None:
    """Print tutorial-specific help information."""
    console.print()
    console.print("[bold]Tutorial Commands[/]")
    console.print()

    commands = [
        ("/chapters", "Show list of all chapters"),
        ("/next", "Go to next chapter"),
        ("/prev", "Go to previous chapter"),
        ("/goto <n>", "Jump to chapter number n"),
        ("/more [n]", "Generate more chapters (default: 3)"),
        ("/topic <subject>", "Start a new tutorial"),
        ("/chat", "Enter chat mode"),
        ("/models", "Show and select available models"),
        ("/provider", "Switch between Ollama and OpenAI"),
        ("/apikey", "Set OpenAI API key"),
        ("/help", "Show this help message"),
        ("/quit", "Exit the tutorial"),
    ]

    for cmd, desc in commands:
        console.print(f"  [bold {THEME['primary']}]{cmd:<18}[/] [dim]{desc}[/]")

    console.print()


def print_chapter_list(tutorial: Tutorial, current_index: int) -> None:
    """Display a list of all chapters with the current one highlighted."""
    console.print()
    console.print(f"[bold]{tutorial.title}[/]")
    console.print(f"[dim]{tutorial.description}[/]")
    console.print()

    table = Table(show_header=True, header_style=f"bold {THEME['primary']}", box=None)
    table.add_column("#", style="dim", width=4)
    table.add_column("Chapter")
    table.add_column("Summary", style="dim")

    for i, chapter in enumerate(tutorial.chapters):
        marker = "*" if i == current_index else " "
        style = f"bold {THEME['primary']}" if i == current_index else ""
        summary = (
            chapter.summary[:50] + "..."
            if len(chapter.summary) > 50
            else chapter.summary
        )
        table.add_row(
            f"{chapter.id}{marker}",
            f"[{style}]{chapter.title}[/]" if style else chapter.title,
            summary,
        )

    console.print(table)
    console.print()
    console.print(
        f"[dim]Current: Chapter {current_index + 1} of {len(tutorial.chapters)}[/]"
    )
    console.print()


def print_chapter_content(
    chapter: Chapter, chapter_index: int, total_chapters: int
) -> None:
    """Display the content of a single chapter."""
    console.print()

    # Chapter header
    header = f"Chapter {chapter.id}: {chapter.title}"
    progress = f"[{chapter_index + 1}/{total_chapters}]"

    console.print(
        Panel(
            f"[bold {THEME['primary']}]{header}[/]  [dim]{progress}[/]",
            border_style=THEME["muted"],
        )
    )

    console.print()

    # Chapter content as markdown
    md = Markdown(chapter.content)
    console.print(md)

    console.print()

    # Navigation hints
    nav_hints: list[str] = []
    if chapter_index > 0:
        nav_hints.append("/prev")
    if chapter_index < total_chapters - 1:
        nav_hints.append("/next")
    nav_hints.append("/chapters")

    console.print(f"[dim]Navigation: {' | '.join(nav_hints)}[/]")
    console.print()


def print_tutorial_welcome() -> None:
    """Print welcome message for tutorial mode."""
    console.print()
    console.print("[bold]Welcome to Janett Tutorials[/]")
    console.print()
    console.print("Enter a topic to generate a comprehensive tutorial.")
    console.print()
    console.print(
        "[dim]Examples: Python basics, REST APIs, Git workflow, React hooks[/]"
    )
    console.print()
    console.print("[dim]Type /help for commands[/]")
    console.print()
