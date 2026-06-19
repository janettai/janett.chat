# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Janett is a terminal CLI (`janett`) that generates structured, chapter-based tutorials and offers a chat mode, backed by local LLMs via Ollama (default) or OpenAI. Pure Python, packaged with hatchling, distributed via PyPI/pipx and a Homebrew formula. Requires Python >= 3.12.

## Commands

This project uses `uv` (see `uv.lock`).

```bash
uv sync --extra dev        # install with dev tools (mypy, ruff, pytest, build, twine)
uv run janett              # run tutorial mode (default)
uv run janett --chat       # run chat mode
uv run janett --version
python -m janett           # equivalent module entry point

uv run ruff check .        # lint
uv run ruff format .       # format (double quotes, 4-space indent, line-length 88 but E501 ignored)
uv run --extra dev mypy src   # type-check (strict mode; tests excluded via override)
uv run --extra dev pytest     # run the test suite (tests/ — no network; uses a fake client)
uv run --extra dev pytest tests/test_tutorial.py::test_navigation_bounds  # single test
```

The tree is kept clean under all four: `ruff check`, `ruff format --check`, `mypy src` (strict), and `pytest` all pass.

To exercise tutorial generation locally, Ollama must be running (`ollama serve`) with a model pulled (`ollama pull llama3.2`); otherwise use OpenAI by setting `OPENAI_API_KEY` or the in-app `/apikey` command.

## Architecture

Single package under `src/janett/`. Two interaction modes share one provider/client abstraction.

- **`config.py`** — all constants and persistence. Defines `PROVIDERS` (ollama/openai base URLs), `OPENAI_MODELS` (pricing table) plus `get_model_pricing()` which falls back to zero-cost for unknown/Ollama models, `THEME` colors, the default and tutorial system prompts (`TUTORIAL_SYSTEM_PROMPT`, `TUTORIAL_CONTINUE_PROMPT`), and read/write of `~/.janett/config.json` (API key **and** persisted provider/model via `get/set_saved_provider` / `get/set_saved_model`). `get_ollama_models()` queries the local Ollama `/api/tags` endpoint at runtime.
- **`chat.py`** — `create_client(provider)` returns an `openai.OpenAI` client pointed at the provider's base URL (Ollama is accessed through OpenAI-compatible API). `ChatSession` holds the message list, token counting (`TokenCounter` via tiktoken), cost stats (zeroed for non-OpenAI providers), and JSON save/load of conversations to `./conversations/` (guarded against path traversal). The module-level `stream_completion()` is the single streaming/markdown-render helper reused by chat mode, the chat UI, and the in-tutorial chat loop.
- **`tutorial.py`** — `TutorialSession` drives generation and chapter navigation. `Tutorial`/`Chapter` are dataclasses. The model is prompted to emit a custom marker format (`===TUTORIAL===`, `===CHAPTER N===`, `---` content delimiters, `===END===`); `_parse_structured_format` parses it via regex, with a JSON fallback (`_parse_json_format`) for backwards compatibility. `generate_more_chapters` feeds prior chapter summaries back in to extend the tutorial.
- **`cli.py`** — entry point and the two REPL loops. `main()` dispatches: `--chat`/`-c` → `chat_main()`, otherwise `tutorial_main()`. Each loop reads input, branches on `/`-prefixed slash commands via `match`/`case`, and treats bare input as a topic (tutorial mode) or a chat message. `ChatUI` and `TutorialUI` own all rendering and call into `ui.py`. `setup_readline()` wires persistent history at `~/.janett/history`.
- **`ui.py`** — stateless `rich`-based print helpers (chapter panels, tables, token stats, help). Holds no session state.

### Key facts

- **Provider model** — both Ollama and OpenAI go through the OpenAI SDK; only the base URL and API key differ. Adding a provider means extending `PROVIDERS` and the `/provider` handler in `cli.py`.
- **Tutorial format is prompt-contracted** — generation reliability depends on the model honoring the `===` marker format. Changing `TUTORIAL_SYSTEM_PROMPT` requires matching the regex in `tutorial.py` (`_parse_structured_format` / `_parse_continuation`).
- **Two layers of chat** — chat mode (`chat_main`) is a full `ChatSession`; tutorial mode's `/chat` spins up a separate ephemeral `ChatSession` reusing the tutorial's provider/model, with its own inline loop. All three streaming paths call `stream_completion()`.
- **Token counts are approximate for non-OpenAI models** — `TokenCounter` uses tiktoken (`encoding_for_model`, falling back to `cl100k_base` for Ollama models), so counts for local models are estimates and their dollar costs are reported as zero.
- **Settings persist** — provider and model selected via `/provider` and `/model` are saved to `~/.janett/config.json` and restored on next launch (`_startup_provider_model()` in `cli.py`).

## Packaging / release

`pyproject.toml` defines the `janett` console script and hatchling wheel (`packages = ["src/janett"]`). Release flow (PyPI then Homebrew) is documented in `docs/HOMEBREW_PUBLISHING.md`; `Formula/janett.rb` is the tap formula and needs its `sha256` filled in after each PyPI publish. `docs/features.md` is a product/roadmap doc (includes an unbuilt web-app plan) — not a description of current code beyond the "Current Features (CLI v0.2.0)" section.
