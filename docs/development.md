# Development

## Setup

```sh
uv sync                                  # Python 3.14 and all dependencies, including dev tools
cp .env.example .env
cp config/example.json config/test.json
```

Add packages with `uv add <package>` (or `uv add --dev <package>` for tools), which updates `pyproject.toml` and `uv.lock`. Commit both files.

## Automated tests

```sh
uv run pytest
```

The tests use `config/example.json` with dummy secrets (see `tests/conftest.py`), so they don't need your `.env` or `test.json`, and they never connect to Discord or MongoDB. They cover:

- config loading and validation, including that the committed `production.json` loads
- channel routing and role checks
- submission text, attachment filtering and sheet export arguments
- WebP conversion and embeds
- the rotation schedule
- command handlers, called directly with mocked interactions:
  ```python
  await cog.webp.callback(cog, interaction, attachment, 80, False)
  ```

Discord has no API for invoking slash commands, and scripting a user account to do it ("self-botting") breaks Discord's Terms of Service. So the tests check what a handler would send, not what Discord shows.

## Testing with the test bot

For anything involving Discord itself (modals, permissions, attachments, embeds), run the test bot against the test server:

```sh
uv run python -m bot
```

With `BOT_TOKEN` set to the test bot's token in `.env`, this loads `config/test.json`. New and removed commands sync on startup, but they can take a moment to appear in Discord. If they don't show up, restart your Discord client.

Before deploying, try one of each in the test server: **Submit Team**, **Submit Team w/ Details**, `/submit`, `/submit_normal`, `/webp`, and `/dr`.

## Code style

[Ruff](https://docs.astral.sh/ruff/) lints and formats the code (settings in `pyproject.toml`; `legacy/` is excluded):

```sh
uv run ruff check --fix .
uv run ruff format .
```

Log with module loggers and `%`-style arguments, e.g. `logger.info("Synced %d commands", count)`, so messages are only formatted when they're actually logged.
