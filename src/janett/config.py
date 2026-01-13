"""Configuration constants for Janett."""

import json
import os
from pathlib import Path

import httpx

# Theme colors - Claude Code inspired minimal palette
THEME = {
    "primary": "#D97706",  # Amber/Orange (Claude accent)
    "secondary": "#A3A3A3",  # Neutral gray
    "success": "#22C55E",  # Green
    "warning": "#FBBF24",  # Yellow
    "error": "#EF4444",  # Red
    "muted": "#737373",  # Muted gray
    "user": "#FFFFFF",  # White for user
    "assistant": "#D97706",  # Claude amber
    "dim": "#525252",  # Dim text
}

# Provider configuration
PROVIDERS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "name": "Ollama (Local)",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": None,  # Set via environment or /apikey command
        "name": "OpenAI",
    },
}

# OpenAI models with pricing (per 1M tokens)
OPENAI_MODELS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "context": 128000},
    "gpt-4o": {"input": 5.00, "output": 15.00, "context": 128000},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00, "context": 128000},
}

# Config file for persisting settings
CONFIG_DIR = Path.home() / ".janett"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config: dict):
    """Save configuration to file."""
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_openai_api_key() -> str | None:
    """Get OpenAI API key from config or environment."""
    # Check environment first
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key
    # Check config file
    config = load_config()
    return config.get("openai_api_key")


def set_openai_api_key(api_key: str):
    """Save OpenAI API key to config file."""
    config = load_config()
    config["openai_api_key"] = api_key
    save_config(config)


def get_ollama_models() -> list[str]:
    """Fetch available models from Ollama."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"].split(":")[0] for m in data.get("models", [])]
            # Remove duplicates while preserving order
            seen = set()
            unique = []
            for m in models:
                if m not in seen:
                    seen.add(m)
                    unique.append(m)
            return unique
    except Exception:
        pass
    return []


DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "llama3.2"

# Timeout for API calls (in seconds)
# Tutorial generation can take longer with local models
API_TIMEOUT = 300  # 5 minutes

DEFAULT_SYSTEM_PROMPT = """You are a helpful, knowledgeable assistant.
When providing code examples, use proper markdown code blocks with language specification.
Be concise but thorough. If you're unsure about something, say so."""

TUTORIAL_SYSTEM_PROMPT = """You are an expert educator who creates comprehensive, structured tutorials.

When a user provides a topic, create a tutorial using this EXACT format:

===TUTORIAL===
Title: [Tutorial title here]
Description: [Brief description]

===CHAPTER 1===
Title: [Chapter title]
Summary: [One line summary]
---
[Full chapter content with explanations and examples]
---

===CHAPTER 2===
Title: [Chapter title]
Summary: [One line summary]
---
[Full chapter content]
---

[Continue with more chapters...]

===END===

Guidelines:
- Create 4-6 chapters
- Each chapter should build on previous ones
- Include code examples where relevant using markdown code blocks
- Make content educational and engaging
- The content section between --- markers can be multiple paragraphs

IMPORTANT: Follow the format exactly with ===TUTORIAL===, ===CHAPTER N===, and ===END=== markers."""

TUTORIAL_CONTINUE_PROMPT = """You are an expert educator continuing a tutorial.

The user has completed these chapters:
{completed_chapters}

Generate {num_chapters} MORE chapters that go deeper into the topic. Start numbering from Chapter {start_num}.

Use this EXACT format:

===CHAPTER {start_num}===
Title: [Chapter title]
Summary: [One line summary]
---
[Full chapter content with explanations and examples]
---

[Continue with more chapters...]

===END===

Guidelines:
- Build on what was already covered
- Go deeper into advanced concepts
- Include practical examples and exercises
- Don't repeat content from previous chapters

IMPORTANT: Start from Chapter {start_num} and follow the format exactly."""

# Directory for saved conversations
SAVE_DIR = Path("./conversations")

# App metadata
APP_NAME = "Janett"
