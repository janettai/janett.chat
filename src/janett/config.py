"""Configuration constants for Janett."""

from pathlib import Path

# Theme colors - Claude Code inspired minimal palette
THEME = {
    "primary": "#D97706",      # Amber/Orange (Claude accent)
    "secondary": "#A3A3A3",    # Neutral gray
    "success": "#22C55E",      # Green
    "warning": "#FBBF24",      # Yellow
    "error": "#EF4444",        # Red
    "muted": "#737373",        # Muted gray
    "user": "#FFFFFF",         # White for user
    "assistant": "#D97706",    # Claude amber
    "dim": "#525252",          # Dim text
}

# Available models with pricing (per 1M tokens) and context limits
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

TUTORIAL_SYSTEM_PROMPT = """You are an expert educator who creates comprehensive, structured tutorials.

When a user provides a topic, respond with a JSON object in this exact format:
{
  "title": "Tutorial Title",
  "description": "Brief description of what this tutorial covers",
  "chapters": [
    {
      "id": 1,
      "title": "Chapter Title",
      "summary": "Brief one-line summary",
      "content": "Full markdown content with explanations, examples, and exercises"
    }
  ]
}

Guidelines:
- Create 4-8 chapters depending on topic complexity
- Each chapter should build on previous ones
- Include practical code examples where relevant
- Use proper markdown formatting in content (headers, code blocks, lists)
- Make content educational and engaging
- Include exercises or practice problems where appropriate

IMPORTANT: Return ONLY valid JSON, no additional text."""

# Directory for saved conversations
SAVE_DIR = Path("./conversations")

# App metadata
APP_NAME = "Janett"
