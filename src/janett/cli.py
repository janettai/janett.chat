"""Command-line interface for Janett."""

import atexit
import readline
import sys
from pathlib import Path

from dotenv import load_dotenv

# Setup persistent command history
HISTORY_FILE = Path.home() / ".janett" / "history"


def setup_readline():
    """Configure readline with persistent history."""
    HISTORY_FILE.parent.mkdir(exist_ok=True)

    # Load existing history
    if HISTORY_FILE.exists():
        try:
            readline.read_history_file(HISTORY_FILE)
        except Exception:
            pass

    # Set history length
    readline.set_history_length(1000)

    # Save history on exit
    atexit.register(lambda: readline.write_history_file(HISTORY_FILE))


from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.status import Status
from rich.text import Text

from janett.chat import ChatSession
from janett.config import (
    APP_NAME,
    OPENAI_MODELS,
    PROVIDERS,
    THEME,
    get_ollama_models,
    get_openai_api_key,
    set_openai_api_key,
)
from janett.tutorial import TutorialSession
from janett.ui import (
    list_saved_conversations,
    print_chapter_content,
    print_chapter_list,
    print_error,
    print_help,
    print_info,
    print_models,
    print_providers,
    print_success,
    print_token_stats,
    print_tutorial_help,
    print_tutorial_welcome,
)

console = Console()


class ChatUI:
    """Chat UI with fixed layout."""

    # Layout constants
    HEADER_LINES = 3  # Header + status + blank line
    INPUT_LINES = 2  # Separator + input line
    MIN_MESSAGE_LINES = 5  # Minimum space for messages

    def __init__(self, session: ChatSession):
        self.session = session
        self.messages: list[dict] = []
        self.console = Console()
        self.height = self.console.height
        self.width = min(self.console.width, 100)

    def _print_header(self):
        """Print header with model info."""
        # App name and model
        header = Text()
        header.append(f"{APP_NAME}", style=f"bold {THEME['primary']}")
        header.append("  ", style="dim")
        header.append(f"{self.session.model}", style=f"dim {THEME['muted']}")

        # Token count if any
        stats = self.session.get_token_stats()
        if stats["total_tokens"] > 0:
            header.append(
                f"  {stats['total_tokens']:,} tokens", style=f"dim {THEME['muted']}"
            )

        self.console.print(header)
        self.console.print()

    def _count_message_lines(self, msg: dict) -> int:
        """Estimate lines a message will take."""
        content = msg["content"]
        # Rough estimate: wrap at width, plus spacing
        lines = len(content) // (self.width - 4) + 1
        return lines + 1  # +1 for spacing

    def _print_welcome(self):
        """Print welcome message when no conversation."""
        self.console.print()
        welcome = Text()
        welcome.append("Hello! ", style="bold")
        welcome.append("How can I help you today?", style="dim")
        self.console.print(welcome)
        self.console.print()
        self.console.print(
            f"[dim {THEME['muted']}]Type a message to start chatting, or /help for commands.[/]"
        )

    def _print_messages(self, max_lines: int):
        """Print conversation messages within line limit."""
        if not self.messages:
            self._print_welcome()
            return

        # Calculate which messages fit
        lines_used = 0
        start_idx = 0

        # Work backwards to find which messages fit
        for i in range(len(self.messages) - 1, -1, -1):
            msg_lines = self._count_message_lines(self.messages[i])
            if lines_used + msg_lines > max_lines:
                start_idx = i + 1
                break
            lines_used += msg_lines

        # Print messages that fit
        for msg in self.messages[start_idx:]:
            match msg["role"]:
                case "user":
                    # User message with "You" label
                    label = Text()
                    label.append("You", style=f"bold {THEME['primary']}")
                    self.console.print(label)
                    self.console.print(f"  {msg['content']}")
                    self.console.print()
                case "assistant":
                    # Assistant message with app name label
                    label = Text()
                    label.append(APP_NAME, style=f"bold {THEME['assistant']}")
                    self.console.print(label)
                    # Indent the markdown content slightly
                    md = Markdown(msg["content"])
                    self.console.print(md)
                    self.console.print()

    def _print_input_area(self):
        """Print the input separator."""
        self.console.print()

    def _get_content_height(self) -> int:
        """Calculate how many lines the current content takes."""
        lines = self.HEADER_LINES

        if not self.messages:
            lines += 4  # Welcome message takes ~4 lines
        else:
            for msg in self.messages:
                lines += self._count_message_lines(msg) + 1  # +1 for label

        return lines

    def refresh(self):
        """Clear and redraw the entire UI."""
        self.console.clear()

        # Recalculate width in case terminal was resized
        self.width = min(self.console.width, 100)

        self._print_header()

        # Print all messages
        self._print_messages(max_lines=999)

    def get_input(self) -> str:
        """Get user input."""
        self._print_input_area()

        try:
            self.console.print(f"[{THEME['primary']}]>[/] ", end="")
            user_input = input()
            return user_input.strip()
        except (KeyboardInterrupt, EOFError):
            self.console.print()
            raise

    def add_user_message(self, content: str):
        """Add user message to history."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        """Add assistant message to history."""
        self.messages.append({"role": "assistant", "content": content})

    def stream_response(self) -> str:
        """Stream response with live updates."""
        stream = self.session.client.chat.completions.create(
            model=self.session.model,
            stream=True,
            messages=self.session.messages,
        )

        full_response = ""

        with Live(console=self.console, refresh_per_second=12, transient=False) as live:
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    live.update(Markdown(full_response))

        self.console.print()
        return full_response

    def clear(self):
        """Clear messages."""
        self.messages = []


class TutorialUI:
    """Tutorial UI with chapter navigation."""

    def __init__(self, session: TutorialSession):
        self.session = session
        self.console = Console()
        self.width = min(self.console.width, 100)

    def _print_header(self):
        """Print header with tutorial info."""
        header = Text()
        header.append(f"{APP_NAME}", style=f"bold {THEME['primary']}")
        header.append(" Tutorial", style="bold")

        # Show provider and model
        provider_name = PROVIDERS.get(self.session.provider, {}).get(
            "name", self.session.provider
        )
        header.append("  ", style="dim")
        header.append(f"{self.session.model}", style=f"dim {THEME['muted']}")
        header.append(f" ({provider_name})", style=f"dim {THEME['muted']}")

        if self.session.tutorial:
            header.append("  ", style="dim")
            header.append(
                f"Ch {self.session.current_chapter_index + 1}/{self.session.tutorial.chapter_count}",
                style=f"dim {THEME['muted']}",
            )

        self.console.print(header)
        self.console.print()

    def refresh(self):
        """Clear and redraw the UI."""
        self.console.clear()
        self._print_header()

        if not self.session.has_tutorial():
            print_tutorial_welcome()
        else:
            chapter = self.session.current_chapter
            if chapter:
                print_chapter_content(
                    chapter,
                    self.session.current_chapter_index,
                    self.session.tutorial.chapter_count,
                )

    def show_chapters(self):
        """Display chapter list."""
        if self.session.tutorial:
            print_chapter_list(
                self.session.tutorial,
                self.session.current_chapter_index,
            )

    def get_input(self) -> str:
        """Get user input."""
        self.console.print()
        try:
            self.console.print(f"[{THEME['primary']}]>[/] ", end="")
            user_input = input()
            return user_input.strip()
        except (KeyboardInterrupt, EOFError):
            self.console.print()
            raise

    def generate_tutorial(self, topic: str) -> tuple[bool, str]:
        """Generate a new tutorial with loading indicator."""
        self.console.print()
        self.console.print(
            f"[{THEME['primary']}]Generating tutorial:[/] [bold]{topic}[/]"
        )

        with Status(
            "[dim]Creating chapters...[/]",
            console=self.console,
            spinner="dots",
        ):
            success, error = self.session.generate_tutorial(topic)

        return success, error

    def generate_more(self, num_chapters: int = 3) -> tuple[bool, str]:
        """Generate additional chapters with loading indicator."""
        self.console.print()
        self.console.print(
            f"[{THEME['primary']}]Generating {num_chapters} more chapters...[/]"
        )

        with Status(
            "[dim]Creating additional content...[/]",
            console=self.console,
            spinner="dots",
        ):
            success, error = self.session.generate_more_chapters(num_chapters)

        return success, error

    def prompt_chapter_selection(self) -> int | None:
        """Show interactive chapter selection prompt."""
        if not self.session.tutorial:
            return None

        self.show_chapters()

        try:
            choice = IntPrompt.ask(
                f"[{THEME['muted']}]Select chapter[/]",
                default=self.session.current_chapter_index + 1,
            )
            return choice - 1  # Convert to 0-based index
        except (KeyboardInterrupt, EOFError):
            return None


def tutorial_main():
    """Main entry point for tutorial mode."""
    load_dotenv()
    setup_readline()

    session = TutorialSession()
    ui = TutorialUI(session)

    # Initial display
    ui.refresh()

    while True:
        try:
            user_input = ui.get_input()
        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print("[dim]Goodbye![/]")
            console.print()
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            match command:
                case "/quit" | "/exit" | "/q":
                    console.print()
                    console.print("[dim]Goodbye![/]")
                    console.print()
                    break
                case "/help":
                    print_tutorial_help()

                case "/topic":
                    if args:
                        success, error = ui.generate_tutorial(args)
                        if success:
                            ui.refresh()
                        else:
                            print_error(f"Failed to generate tutorial: {error}")
                    else:
                        topic = Prompt.ask(f"[{THEME['muted']}]Enter topic[/]")
                        if topic:
                            success, error = ui.generate_tutorial(topic)
                            if success:
                                ui.refresh()
                            else:
                                print_error(f"Failed to generate tutorial: {error}")

                case "/chapters":
                    if session.has_tutorial():
                        choice = ui.prompt_chapter_selection()
                        if choice is not None and session.go_to_chapter(choice):
                            ui.refresh()
                    else:
                        print_info("No tutorial loaded. Enter a topic to start.")

                case "/next":
                    if session.has_tutorial():
                        if session.next_chapter():
                            ui.refresh()
                        else:
                            print_info("You're at the last chapter.")
                    else:
                        print_info("No tutorial loaded. Enter a topic to start.")

                case "/prev":
                    if session.has_tutorial():
                        if session.prev_chapter():
                            ui.refresh()
                        else:
                            print_info("You're at the first chapter.")
                    else:
                        print_info("No tutorial loaded. Enter a topic to start.")

                case "/goto":
                    if session.has_tutorial():
                        try:
                            chapter_num = int(args)
                            if session.go_to_chapter(chapter_num - 1):
                                ui.refresh()
                            else:
                                print_error(
                                    f"Invalid chapter. Use 1-{session.tutorial.chapter_count}"
                                )
                        except ValueError:
                            print_error("Please provide a valid chapter number.")
                    else:
                        print_info("No tutorial loaded. Enter a topic to start.")

                case "/refresh":
                    ui.refresh()

                case "/more":
                    if session.has_tutorial():
                        # Parse optional number of chapters
                        num = 3
                        if args:
                            try:
                                num = int(args)
                                num = max(1, min(num, 5))  # Clamp between 1-5
                            except ValueError:
                                pass

                        success, error = ui.generate_more(num)
                        if success:
                            ui.refresh()
                            print_success(f"Added {num} new chapters!")
                        else:
                            print_error(f"Failed to generate more chapters: {error}")
                    else:
                        print_info("No tutorial loaded. Enter a topic first.")

                case "/chat":
                    # Enter chat mode within tutorial (uses same provider/model)
                    console.print()
                    console.print(
                        "[bold]Chat Mode[/] [dim](type /back to return to tutorial)[/]"
                    )
                    console.print()

                    chat_session = ChatSession(
                        model=session.model,
                        provider=session.provider,
                    )

                    while True:
                        try:
                            console.print(f"[{THEME['primary']}]>[/] ", end="")
                            chat_input = input().strip()
                        except (KeyboardInterrupt, EOFError):
                            ui.refresh()
                            break

                        if not chat_input:
                            continue

                        if chat_input.lower() in ("/back", "/exit"):
                            ui.refresh()
                            break

                        # Get response from chat
                        chat_session.add_user_msg(chat_input)
                        console.print()

                        try:
                            stream = chat_session.client.chat.completions.create(
                                model=chat_session.model,
                                stream=True,
                                messages=chat_session.messages,
                            )

                            full_response = ""
                            with Live(
                                console=console, refresh_per_second=12, transient=False
                            ) as live:
                                for chunk in stream:
                                    if chunk.choices[0].delta.content is not None:
                                        full_response += chunk.choices[0].delta.content
                                        live.update(Markdown(full_response))

                            console.print()
                            chat_session.add_assistant_message(full_response)
                        except Exception as e:
                            chat_session.messages.pop()
                            print_error(f"API Error: {e}")

                case "/models":
                    print_models(session.model, session.provider)

                    # Get available models based on provider
                    if session.provider == "ollama":
                        models = get_ollama_models()
                    else:
                        models = list(OPENAI_MODELS.keys())

                    if models:
                        new_model = Prompt.ask(
                            f"[{THEME['muted']}]Select model[/]",
                            default=session.model,
                        )
                        if new_model in models:
                            session.model = new_model
                            ui.refresh()
                            print_success(f"Model changed to {new_model}")
                        elif new_model != session.model:
                            print_error(f"Model not found: {new_model}")

                case "/provider":
                    print_providers(session.provider)

                    new_provider = Prompt.ask(
                        f"[{THEME['muted']}]Select provider[/]",
                        choices=list(PROVIDERS.keys()),
                        default=session.provider,
                    )

                    if new_provider != session.provider:
                        # Check for API key if switching to OpenAI
                        if new_provider == "openai" and not get_openai_api_key():
                            print_error(
                                "OpenAI API key not set. Use /apikey to set it first."
                            )
                        else:
                            # Set default model for the provider
                            if new_provider == "ollama":
                                models = get_ollama_models()
                                default_model = models[0] if models else "llama3.2"
                            else:
                                default_model = "gpt-4o-mini"

                            session.set_provider(new_provider, default_model)
                            ui.refresh()
                            print_success(
                                f"Switched to {PROVIDERS[new_provider]['name']}"
                            )

                case "/apikey":
                    console.print()
                    current_key = get_openai_api_key()
                    if current_key:
                        masked = current_key[:8] + "..." + current_key[-4:]
                        console.print(f"[dim]Current key: {masked}[/]")

                    new_key = Prompt.ask(
                        f"[{THEME['muted']}]Enter OpenAI API key[/]",
                        password=True,
                    )

                    if new_key:
                        set_openai_api_key(new_key)
                        print_success("API key saved to ~/.janett/config.json")
                    else:
                        print_info("Cancelled.")

                case _:
                    print_error(f"Unknown command: {command}")
                    print_info("Type /help for available commands.")

            continue

        # If no tutorial exists, treat input as a topic
        if not session.has_tutorial():
            success, error = ui.generate_tutorial(user_input)
            if success:
                ui.refresh()
            else:
                print_error(f"Failed to generate tutorial: {error}")
        else:
            # If tutorial exists, ask if user wants a new topic
            if Confirm.ask(
                f"[{THEME['warning']}]Start new tutorial on '{user_input}'?[/]",
                default=False,
            ):
                session.reset()
                success, error = ui.generate_tutorial(user_input)
                if success:
                    ui.refresh()
                else:
                    print_error(f"Failed to generate tutorial: {error}")


def main():
    """Main entry point for the CLI."""
    # Version flag
    if "--version" in sys.argv or "-v" in sys.argv:
        from janett import __version__

        print(f"janett {__version__}")
        return

    # Chat mode requires explicit flag, tutorial is default
    if "--chat" in sys.argv or "-c" in sys.argv:
        chat_main()
        return

    # Default to tutorial mode
    tutorial_main()


def chat_main():
    """Entry point for chat mode."""
    load_dotenv()
    setup_readline()

    session = ChatSession()
    ui = ChatUI(session)

    # Initial display
    ui.refresh()

    while True:
        try:
            user_input = ui.get_input()
        except (KeyboardInterrupt, EOFError):
            stats = session.get_token_stats()
            stats["messages"] = session.get_message_count()
            console.print()
            if stats["total_tokens"] > 0:
                console.print(
                    f"[dim]{stats.get('messages', 0)} messages • {stats['total_tokens']:,} tokens • ${stats['total_cost']:.4f}[/]"
                )
            console.print()
            console.print("[dim]Goodbye.[/]")
            console.print()
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            match command:
                case "/quit" | "/exit" | "/q":
                    stats = session.get_token_stats()
                    stats["messages"] = session.get_message_count()
                    console.print()
                    if stats["total_tokens"] > 0:
                        console.print(
                            f"[dim]{stats.get('messages', 0)} messages • {stats['total_tokens']:,} tokens • ${stats['total_cost']:.4f}[/]"
                        )
                    console.print()
                    console.print("[dim]Goodbye.[/]")
                    console.print()
                    break

                case "/help":
                    print_help()

                case "/clear":
                    console.print()
                    if Confirm.ask(
                        f"[{THEME['warning']}]Clear conversation history?[/]",
                        default=False,
                    ):
                        session.clear_history()
                        ui.clear()
                        ui.refresh()
                        print_success("Conversation cleared.")
                    else:
                        print_info("Cancelled.")

                case "/tokens":
                    stats = session.get_token_stats()
                    print_token_stats(stats)

                case "/model":
                    print_models(session.model)
                    new_model = Prompt.ask(
                        f"[{THEME['muted']}]Enter model name[/]", default=session.model
                    )
                    if session.set_model(new_model):
                        print_success(f"Model changed to {new_model}")
                        ui.refresh()  # Refresh to show new model
                    else:
                        print_error(f"Unknown model: {new_model}")

                case "/system":
                    console.print()
                    console.print(
                        f"[{THEME['muted']}]Enter new system prompt (or 'cancel'):[/]"
                    )
                    new_prompt = Prompt.ask("[dim]Prompt[/]")
                    if new_prompt.lower() != "cancel" and new_prompt:
                        session.set_system_prompt(new_prompt)
                        ui.clear()
                        ui.refresh()
                        print_success("System prompt updated.")
                    else:
                        print_info("Cancelled.")

                case "/save":
                    if not args:
                        args = Prompt.ask(
                            f"[{THEME['muted']}]Filename[/]", default="conversation"
                        )
                    filepath = session.save_conversation(args)
                    print_success(f"Saved to {filepath}")

                case "/load":
                    if not args:
                        list_saved_conversations()
                        args = Prompt.ask(f"[{THEME['muted']}]Filename[/]")
                    if session.load_conversation(args):
                        # Rebuild UI messages from session
                        ui.clear()
                        for msg in session.messages[1:]:  # Skip system message
                            if msg["role"] == "user":
                                ui.add_user_message(msg["content"])
                            elif msg["role"] == "assistant":
                                ui.add_assistant_message(msg["content"])
                        ui.refresh()
                        print_success(f"Loaded: {args}")
                        print_info(
                            f"Model: {session.model} | Messages: {session.get_message_count()}"
                        )
                    else:
                        print_error(f"Could not load: {args}")

                case "/list":
                    list_saved_conversations()

                case "/refresh":
                    ui.refresh()

                case _:
                    print_info("Type /help for available commands.")
                    print_error(f"Unknown command: {command}")

            continue

        # Add user message
        ui.add_user_message(user_input)
        session.add_user_msg(user_input)

        # Count input tokens
        input_tokens = session.token_counter.count_messages(session.messages)
        session.total_input_tokens += input_tokens

        # Refresh to show user message
        ui.refresh()

        # Get and stream response
        try:
            response = ui.stream_response()
            ui.add_assistant_message(response)

            # Count output tokens
            out_tokens = session.token_counter.count(response)
            session.total_output_tokens += out_tokens
            session.add_assistant_message(response)

        except Exception as e:
            session.messages.pop()  # Remove failed user message
            ui.messages.pop()  # Remove from UI too
            print_error(f"API Error: {e}")


if __name__ == "__main__":
    main()
