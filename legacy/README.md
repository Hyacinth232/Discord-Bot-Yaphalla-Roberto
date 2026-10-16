# Legacy Roberto

Archived code from before the slash-command rewrite. Nothing in here is imported by the running bot.

The last working version of the full bot is tagged `pre-rewrite`:

```
git checkout pre-rewrite
```

## What was retired

- **`!` prefix commands**: `!submit`, `!subn`, `!subp`, `!collect`, `!webp`, `!lwebp`, `!souschef`, `!amaryllis`
- **Formation builder**: `/add_*`, `/remove_list`, `/swap_*`, `/move_unit`, `/mirror`, `/display`, `/view`, `/see`, `/set_*`, `/show_*`, `/make_transparent`, the saved formation commands, `/yap_map`, `/yap_base_hex` (`bot/core/commands_backend.py`, `bot/database/users.py`, `bot/image/hex.py`, `bot/image/image_loader.py`, `bot/image/image_maker.py`, `bot/services/formation_image_service.py`, `assets/`, `data/aliases.json`, `data/hexes.json`, `data/maps.json`)
- **Image recognition**: formation extraction (`bot/image/analyze_image.py`), OCR damage extraction (`bot/image/damage_extractor.py`), the "Report Image Misidentification" button, and the spam-thread logging in `bot/submission/submit_collect.py`
- **`/emoji`, `/emojify`**

Files that were rewritten rather than removed (config, utils, database, modals, views, embeds, google_sheets, ...) are kept here as they were before the rewrite. `requirements.txt` and `Aptfile` are the old dependency lists, which include OpenCV, Tesseract and pygame.

Paths inside this code still assume it lives at the repository root, so restore it from the tag rather than running it from here.
