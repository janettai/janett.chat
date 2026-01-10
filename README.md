# Janett

A beautiful terminal chat interface for OpenAI models.

## Features

- **Streaming responses** - See AI responses as they're generated
- **Multiple models** - Switch between GPT-4o, GPT-4 Turbo, GPT-3.5, and more
- **Token tracking** - Monitor usage and costs in real-time
- **Conversation management** - Save and load chat sessions
- **Rich terminal UI** - Beautiful colors, panels, and formatting
- **Markdown rendering** - Code blocks, lists, and formatting rendered in terminal

## Installation

```bash
pip install janett
```

## Quick Start

1. Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Or create a `.env` file:

```
OPENAI_API_KEY=your-api-key
```

2. Start chatting:

```bash
janett
```

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/model` | Change the AI model |
| `/tokens` | Show token usage and cost |
| `/save <name>` | Save conversation to file |
| `/load <name>` | Load a saved conversation |
| `/list` | List saved conversations |
| `/system` | Set a custom system prompt |
| `/clear` | Clear conversation history |
| `/quit` | Exit the chat |

## Supported Models

| Model | Input Cost | Output Cost | Context |
|-------|-----------|-------------|---------|
| gpt-4o-mini | $0.15/1M | $0.60/1M | 128K |
| gpt-4o | $5.00/1M | $15.00/1M | 128K |
| gpt-4-turbo | $10.00/1M | $30.00/1M | 128K |
| gpt-3.5-turbo | $0.50/1M | $1.50/1M | 16K |

## Programmatic Usage

You can also use Janett as a library:

```python
from janett import ChatSession

session = ChatSession(model="gpt-4o-mini")
response = session.get_response("Hello!", stream=False)
print(response)

# Get token stats
stats = session.get_token_stats()
print(f"Total cost: ${stats['total_cost']:.4f}")
```

## Development

```bash
# Clone the repository
git clone https://github.com/janettai/janett.chat.git
cd janett.chat

# Install dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/

# Run type checking
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
