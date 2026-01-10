"""Terminal UI components for Janett."""

import json

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text

from janett import __version__
from janett.config import (
    APP_NAME,
    MODELS,
    SAVE_DIR,
    THEME,
)

console = Console()


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
    info.add_row("Version", f"[dim]{__version__}[/]")

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
