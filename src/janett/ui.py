"""Terminal UI components for Janett."""

import json

from rich.console import Console

from janett.config import (
    MODELS,
    SAVE_DIR,
    THEME,
)

console = Console()


def print_help():
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


def print_token_stats(stats: dict):
    """Print token usage statistics with minimal styling."""
    console.print()
    console.print(f"[bold]Token Usage[/] [dim]({stats['model']})[/]")
    console.print()

    console.print(f"  [dim]Input[/]    {stats['input_tokens']:,} tokens  [dim](${stats['input_cost']:.4f})[/]")
    console.print(f"  [dim]Output[/]   {stats['output_tokens']:,} tokens  [dim](${stats['output_cost']:.4f})[/]")
    console.print(f"  [bold]Total[/]    {stats['total_tokens']:,} tokens  [bold {THEME['success']}](${stats['total_cost']:.4f})[/]")

    context_pct = (stats['context_used'] / stats['context_limit']) * 100
    context_style = THEME['success'] if context_pct < 50 else (THEME['warning'] if context_pct < 80 else THEME['error'])
    console.print()
    console.print(f"  [dim]Context[/]  [{context_style}]{stats['context_used']:,} / {stats['context_limit']:,} ({context_pct:.1f}%)[/]")
    console.print()


def print_models(current_model: str):
    """Print available models with minimal styling."""
    console.print()
    console.print("[bold]Models[/] [dim](per 1M tokens)[/]")
    console.print()

    for model, info in MODELS.items():
        if model == current_model:
            console.print(f"  [bold {THEME['primary']}]{model}[/] [dim]in:${info['input']:.2f} out:${info['output']:.2f} ctx:{info['context']:,}[/] [bold {THEME['success']}]*[/]")
        else:
            console.print(f"  [dim]{model}[/] [dim]in:${info['input']:.2f} out:${info['output']:.2f} ctx:{info['context']:,}[/]")

    console.print()


def list_saved_conversations():
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
            console.print(f"  [bold]{filepath.stem}[/] [dim]{saved_at} • {msg_count} msgs • {model}[/]")
        except Exception:
            console.print(f"  [bold]{filepath.stem}[/] [red]Error loading[/]")

    console.print()


def print_success(message: str):
    """Print success message."""
    console.print(f"[{THEME['success']}]✓[/] {message}")


def print_error(message: str):
    """Print error message with minimal styling."""
    console.print()
    console.print(f"[{THEME['error']}]Error:[/] {message}")
    console.print()


def print_info(message: str):
    """Print info message."""
    console.print(f"[{THEME['muted']}]{message}[/]")
