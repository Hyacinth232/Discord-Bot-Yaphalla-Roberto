# Roberto

Yaphalla's Discord bot. Roberto forwards team and stage submissions from the kitchen channels to the 📌 channels and the tracking sheet, serves the boss infographics, rotates which Dream Realm boss channels are visible each day, and has a few small tools.

Roberto uses only slash commands and message context menus (right-click a message → **Apps**). It has no `!` prefix commands and needs no privileged gateway intents.

## Quick start

Requires [uv](https://docs.astral.sh/uv/). uv installs the right Python version for you.

```sh
uv sync                                  # create .venv with Python 3.14 and all dependencies
cp .env.example .env                     # then fill in BOT_TOKEN, MONGO_URI, GOOGLE_SA_JSON
cp config/example.json config/test.json  # then fill in your test server's IDs
uv run python -m bot
```

Locally the bot loads `config/test.json`; on Heroku it loads `config/production.json`. Use a separate test bot token in `.env` so you never run against the production server by accident.

## Checks

```sh
uv run pytest            # tests; no Discord or database connection needed
uv run ruff check .      # lint
uv run ruff format .     # format
```

CI runs all three on every push and pull request.

## Documentation

- [Commands](docs/commands.md): what each command does and who can use it
- [Configuration](docs/configuration.md): config files, environment variables, and starting a new season
- [Architecture](docs/architecture.md): how the code is organized and how a submission flows through it
- [Development](docs/development.md): testing locally and with the test bot
- [Deployment](docs/deployment.md): Heroku setup and releasing

Code from before the slash-command rewrite (the formation builder, image recognition and `!` commands) is archived in [`legacy/`](legacy/README.md).
