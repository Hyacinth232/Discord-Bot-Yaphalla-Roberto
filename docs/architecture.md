# Architecture

```
bot/
├── __main__.py          Entry point (python -m bot): logging, signal handling, start
├── core/
│   ├── client.py        Roberto (commands.Bot): creates services, loads cogs, syncs commands, handles command errors
│   ├── config.py        Settings models and loading (see configuration.md)
│   ├── channels.py      Kitchen channel → public/private channel routing
│   ├── checks.py        Role checks for commands
│   ├── enum_classes.py
│   └── utils.py         Discord fetch helpers, emojis, timestamps
├── cogs/                One cog per feature area; each command lives here
│   ├── submissions.py   Submit context menus and slash commands
│   ├── infographics.py  Boss guides and /yap_update_image
│   ├── utilities.py     WebP conversion and timestamps
│   ├── staff.py         /benchmark, /souschef
│   └── rotation.py      Dream Realm channel rotation task
├── submission/
│   ├── submission.py    Submission: posts to channels and the sheet
│   └── google_sheets.py Tracking sheet export
├── services/            Small services over the database
├── database/database.py MongoDB (pymongo's async client)
├── image/webp_converter.py
└── ui/                  Modals, views and embeds
```

## Design

- **Cogs own commands.** Each feature area is a cog loaded as an extension in `Roberto.setup_hook`, so it can be read and changed on its own. Context menus can't be declared with decorators inside a cog, so cogs create them in `__init__` and register them in `cog_load`.
- **Modals only collect input.** A modal parses its fields into a dataclass (`SheetDetails`, `StageDetails`) or text and passes it to a callback from the cog. The cog decides what to do with it, so the modals don't need to know about submissions.
- **One error handler.** `RobertoCommandTree.on_error` turns failed role checks into a "no permission" reply, and logs anything else while sending the user a generic error.
- **Config is checked at startup.** Pydantic models reject unknown keys and missing channels before the bot connects, rather than failing on the first command that needs them.
- **Commands are global.** Every startup syncs the command tree globally and clears any commands registered to the server alone. Removing a command from the code removes it from Discord on the next start.
- **No privileged intents.** Context menus receive the target message (content and attachments included) in the interaction, and members are fetched when they're not cached.

## A submission, start to finish

Taking **Submit Team w/ Details** as the example:

1. `Submissions.submit_team_with_details` checks that the message is in a kitchen channel that isn't AFK, then opens a `SheetDetailsModal`.
2. When the modal is submitted, it defers the interaction and calls back with a `SheetDetails`.
3. The cog builds a `Submission`, which takes the message's images and videos (from the snapshot, for forwarded messages) and its text.
4. `Submission.register` looks up display names, takes the next ID from the boss's counter in MongoDB, and adds 📝 to the message.
5. The user gets an ephemeral thank-you. `Submission.forward` posts the embeds and files to the boss's private channel (from `channels.to_channel_type_id`).
6. `Submission.export_to_sheet` appends a row to the boss's tab and the combined "Roberto" tab. If that fails, Amaryllis gets a DM.

`/submit` also posts to the public channel first, and links to that post because there's no original message.
