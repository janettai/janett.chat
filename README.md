# Janett

Learn anything with AI-generated tutorials, right in your terminal.

Janett creates structured, chapter-based tutorials on any topic using local AI (free & private) or OpenAI.

## Installation

### Easy Install (Recommended)

**macOS/Linux:**
```bash
# 1. Install pipx (one-time setup)
brew install pipx
pipx ensurepath

# 2. Install Janett
pipx install janett
```

**Windows:**
```bash
# 1. Install pipx (one-time setup)
scoop install pipx
pipx ensurepath

# 2. Install Janett
pipx install janett
```

### Set Up Local AI (Free & Private)

Janett works best with Ollama, which runs AI models on your computer for free:

**macOS:**
```bash
brew install ollama
ollama pull llama3.2
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

**Windows:**
Download from [ollama.com/download](https://ollama.com/download), then:
```bash
ollama pull llama3.2
```

### For Developers

```bash
pip install janett
```

## Getting Started

1. **Start Ollama** (if using local AI):
   ```bash
   ollama serve
   ```

2. **Run Janett**:
   ```bash
   janett
   ```

3. **Enter a topic** like "Python basics" or "How to cook pasta"

4. **Navigate chapters** with `/next`, `/prev`, or `/chapters`

5. **Want more?** Type `/more` to generate additional chapters

## Commands

| Command | What it does |
|---------|--------------|
| `/next` | Go to next chapter |
| `/prev` | Go to previous chapter |
| `/chapters` | See all chapters |
| `/goto 3` | Jump to chapter 3 |
| `/more` | Add more chapters |
| `/topic cooking` | Start new tutorial |
| `/chat` | Switch to chat mode |
| `/help` | Show all commands |
| `/quit` | Exit |

## Using OpenAI Instead

If you prefer OpenAI (requires API key):

```bash
# In Janett, run:
/apikey
# Enter your OpenAI API key

/provider
# Select: openai
```

Get an API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## Example

```
$ janett

Janett Tutorial  llama3.2 (Ollama)

Welcome to Janett Tutorials

Enter a topic to generate a comprehensive tutorial.

> photography for beginners

Generating tutorial: photography for beginners
Creating chapters...

┌─────────────────────────────────────────────────────┐
│ Chapter 1: Understanding Your Camera  [1/5]        │
└─────────────────────────────────────────────────────┘

Photography begins with understanding your camera...

> /next     # Continue to chapter 2
> /more     # Generate more chapters
> /chat     # Ask questions about the topic
```

## Tips

- **Better results**: Use specific topics like "Python lists and loops" instead of just "Python"
- **Go deeper**: Use `/more` after finishing to generate advanced chapters
- **Ask questions**: Use `/chat` to ask about anything in the tutorial
- **Bigger models**: Try `ollama pull llama3.1` for more detailed tutorials

## Troubleshooting

**"Failed to generate tutorial"**
- Make sure Ollama is running: `ollama serve`
- Check you have a model: `ollama list`

**"No models found"**
- Pull a model: `ollama pull llama3.2`

**Slow generation**
- First run downloads the model (~2GB)
- Subsequent runs are faster

## Uninstall

```bash
pipx uninstall janett
```

## License

MIT License - free to use and modify.

---

Made with AI, for humans who want to learn.
