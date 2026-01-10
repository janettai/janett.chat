"""Configuration constants for Janett."""

from pathlib import Path

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

# Directory for saved conversations
SAVE_DIR = Path("./conversations")

# App metadata
APP_NAME = "Janett"
