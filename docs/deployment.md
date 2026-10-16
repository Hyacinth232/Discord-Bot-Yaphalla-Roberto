# Deployment

Roberto runs on Heroku as the `yaphalla-bot` app: one `worker` dyno running `python -m bot` (see `Procfile`).

## How Heroku builds it

The `heroku/python` buildpack sees `uv.lock` and installs with uv. It uses the Python version in `.python-version` and the exact package versions in `uv.lock`. No other buildpacks are needed.

```sh
heroku buildpacks -a yaphalla-bot     # should list only heroku/python
```

## Config vars

Set the [environment variables](configuration.md#environment-variables) as config vars:

```sh
heroku config -a yaphalla-bot                          # list
heroku config:set -a yaphalla-bot MONGO_URI='...'      # set (restarts the dyno)
```

`ENVIRONMENT` doesn't need setting: Heroku sets `DYNO`, which selects `config/production.json`.

## Releasing

1. Check that `uv run pytest` passes, and try the change with the test bot.
2. Push to `main`. Deploy by whichever method the app uses: GitHub integration, or `git push heroku main`.
3. Watch it start:
   ```sh
   heroku logs --tail -a yaphalla-bot
   heroku ps -a yaphalla-bot
   ```
   A healthy start logs "Synced N global application commands" and "Bot … started", and Amaryllis gets a DM listing the servers.

Heroku restarts dynos about once a day and on every deploy, stopping them with `SIGTERM`. Roberto handles that by closing its Discord connection and database client cleanly.

## Discord Developer Portal

Under **Bot → Privileged Gateway Intents**, all three intents (Presence, Server Members, Message Content) can stay off. When inviting the bot, it needs these permissions:

- View Channels, Send Messages, Embed Links, Attach Files, Add Reactions, Read Message History
- Manage Roles, so the rotation can edit channel permission overwrites
- Mention @everyone, @here and All Roles, if the pinged roles aren't mentionable
