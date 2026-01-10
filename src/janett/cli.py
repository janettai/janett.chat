"""Command-line interface for Janett."""

from dotenv import load_dotenv
from rich.prompt import Confirm, Prompt

from janett.chat import ChatSession
from janett.config import THEME
from janett.ui import (
    console,
    get_prompt,
    list_saved_conversations,
    print_error,
    print_goodbye,
    print_header,
    print_help,
    print_info,
    print_models,
    print_success,
    print_token_stats,
    print_user_message,
    print_welcome,
)


def main():
    """Main entry point for the CLI."""
    load_dotenv()

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
                new_prompt = Prompt.ask("[dim]Prompt[/]")
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

        # Get response
        console.print()
        session.get_response(user_input)


if __name__ == "__main__":
    main()
