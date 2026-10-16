# Commands

Context menus are on messages: right-click (or long-press on mobile) → **Apps**.

"Waiter" and "stage" mean the roles under `roles` in the [environment config](configuration.md). Server administrators and Amaryllis pass every role check.

## Submissions

Team submissions work in kitchen channels other than AFK. Each submission gets an ID, is posted to the boss's private 📌 channel, and the original message gets a 📝 reaction.

| Command | Who | What it does |
|---|---|---|
| **Submit Team** (context menu) | Anyone | Submits the message as-is |
| **Edit & Submit Team** (context menu) | Anyone | Lets you edit the message's text, then submits it |
| **Submit Team w/ Details** (context menu) | Anyone | Asks for credits, damage, resonance, ascension and notes, then submits and adds a row to the tracking sheet |
| `/submit file1 … file5` | Anyone | Same as **Submit Team w/ Details** for uploaded files, and also posts the submission to the boss's public channel |
| `/submit_normal`, `/submit_phantimal` | Stage | AFK channel only. Asks for the stage, charms/gear, timings, replays and notes |

## Boss guides

| Command | What it does |
|---|---|
| `/paragon`, `/charms` | Shows that infographic |
| `/dream-realm` (`/dr`), `/primal-lord` (`/pl`), `/ravaged-realm` | Lists the game mode's boss channels with a dropdown of their infographics |
| `/yap_update_image key text` (waiter) | Replaces an infographic. `:yapName:` in the text becomes that emoji |

## Tools

| Command | What it does |
|---|---|
| `/webp image [quality] [lossless]` | Converts an image to WebP and posts it with a copyable link. Quality is 20–100 (default 80) |
| **Convert to WebP** / **Convert to Lossless WebP** (context menu) | Converts the first image in a message |
| `/get_timestamp month day [year] [hour]` | Turns a UTC date and hour into a Discord timestamp |
| `/time_now` | Shows the current time as a Discord timestamp |

## Staff

| Command | Who | What it does |
|---|---|---|
| `/benchmark` | Waiter | Pings the benchmark role |
| `/souschef message [file1…file3]` | Waiter | Pings the sous chef role with your message and files. Public kitchen channels, plus `souschef_extra_channel_ids` |

## Automatic

Every 6 hours Roberto shows today's and tomorrow's Dream Realm boss channels to `@everyone` and hides the others. The order comes from `game_modes.dream_realm`, counted in days from `start_date` (see [configuration](configuration.md#starting-a-new-season)).
