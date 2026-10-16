# Configuration

Settings come from three places, merged at startup by `bot/core/config.py`:

| Source | Holds | Committed? |
|---|---|---|
| `config/shared.json` | Game data, the same for every server: season, rotation start date, boss lists | Yes |
| `config/<environment>.json` | One Discord server's IDs: roles, channels, spreadsheet | `production.json` yes, `test.json` no |
| Environment variables (`.env` locally, config vars on Heroku) | Secrets | No |

The environment is `ENVIRONMENT` if set, otherwise `production` on Heroku and `test` anywhere else. `config/example.json` is a template for `test.json`, and the tests use it too.

Mistakes in these files stop the bot at startup with an error naming the problem. That covers unknown keys (usually typos), a key set in both `shared.json` and the environment file, and a Dream Realm boss with no channels.

## Environment variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Discord bot token. Use the test bot's token locally |
| `MONGO_URI` | MongoDB connection string (submission counters and infographic links) |
| `GOOGLE_SA_JSON` | Google service account key as one line of JSON, used to write to the tracking sheet |
| `ENVIRONMENT` | Optional. Which `config/<name>.json` to load |

See `.env.example`.

## `shared.json`

| Key | Description |
|---|---|
| `amaryllis_id` | Bot owner's user ID: passes every role check, and gets the startup DM and sheet-export error DMs |
| `season` | Shown in boss guide titles, e.g. "S8 Dream Realm Bosses" |
| `start_date` | UTC start of the season; day 0 of the Dream Realm rotation |
| `game_modes` | Boss names for `dream_realm` (in rotation order), `primal_lords`, `ravaged_realm` and `titan_reaver` |

## Environment files

| Key | Description |
|---|---|
| `server_id` | The Discord server |
| `spreadsheet_id` | Optional. Tracking sheet ID; without it, sheet export is skipped |
| `souschef_extra_channel_ids` | Optional. Channels besides the public kitchen channels where `/souschef` works |
| `roles` | `waiter` and `stage` (lists of role IDs allowed to use those commands), plus `benchmark` and `souschef` (the roles pinged) |
| `afk` | The public AFK channel and the private `normal` and `phantimal` channels |
| `bosses` | Every kitchen channel, by boss name: `{ "public": id, "private": id }` |

Boss names are used as the submission counter keys and as tab names in the tracking sheet. Renaming a boss starts its submission IDs over and sends its rows to a new tab.

## Starting a new season

1. In `shared.json`, set `season` and `start_date`, and update the boss lists in `game_modes`. The `dream_realm` order is the rotation order.
2. In `production.json` (and your `test.json`), add the new bosses' channels under `bosses`. Remove channels you no longer accept submissions in.
3. Run `uv run pytest`. It checks that the committed configs load.
4. Set the new bosses' infographics with `/yap_update_image` once the bot is running.

To find an ID in Discord, turn on **Settings → Advanced → Developer Mode**, then right-click a channel, role or user → **Copy ID**.
