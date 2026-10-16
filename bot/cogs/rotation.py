"""Daily rotation of which Dream Realm boss channels are visible."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

from bot.core.config import app_settings
from bot.core.utils import datetime_now, get_or_fetch_channel, get_or_fetch_server

if TYPE_CHECKING:
    from bot.core.client import Roberto

logger = logging.getLogger(__name__)

# Season start dates (UTC), for reference:
# s4 2025-05-23, s5 2025-09-26, s6 2026-01-30, s7 2026-05-29, s8 2026-09-23


def visible_bosses(bosses: list[str], start_date: datetime, now: datetime) -> set[str]:
    """Today's and tomorrow's bosses, cycling through the list from start_date."""
    elapsed_days = (now - start_date).days
    return {bosses[elapsed_days % len(bosses)], bosses[(elapsed_days + 1) % len(bosses)]}


class Rotation(commands.Cog):
    def __init__(self, bot: Roberto):
        self.bot = bot

    async def cog_load(self):
        self.rotate_channels.start()

    async def cog_unload(self):
        self.rotate_channels.cancel()

    @tasks.loop(hours=6)
    async def rotate_channels(self):
        """Show today's and tomorrow's Dream Realm boss channels and hide the rest."""
        server = await get_or_fetch_server(self.bot, app_settings.server_id)
        if server is None:
            logger.error("Server %s not found", app_settings.server_id)
            return

        bosses = app_settings.game_modes.dream_realm
        if not bosses:
            logger.error("No channels configured to rotate")
            return

        visible = visible_bosses(bosses, app_settings.start_date, datetime_now())
        logger.info("Rotating channels: visible=%s", sorted(visible))

        for boss_name in bosses:
            await self._set_visibility(server, boss_name, boss_name in visible)

    @rotate_channels.before_loop
    async def before_rotate_channels(self):
        await self.bot.wait_until_ready()

    async def _set_visibility(self, server: discord.Guild, boss_name: str, visible: bool):
        """Set @everyone's view permission on a boss's public and private channels."""
        # Config validation guarantees every Dream Realm boss has channels
        channels = app_settings.bosses[boss_name]
        public_chan = await get_or_fetch_channel(server, channels.public)
        private_chan = await get_or_fetch_channel(server, channels.private)
        if public_chan is None or private_chan is None:
            logger.warning("Channels for %s not found", boss_name)
            return

        try:
            # overwrites_for returns a copy, so other permissions are preserved
            public_overwrite = public_chan.overwrites_for(server.default_role)
            private_overwrite = private_chan.overwrites_for(server.default_role)

            public_overwrite.view_channel = visible
            private_overwrite.view_channel = visible
            private_overwrite.send_messages = False

            await public_chan.set_permissions(server.default_role, overwrite=public_overwrite)
            await private_chan.set_permissions(server.default_role, overwrite=private_overwrite)
            logger.info("Set view_channel to %s for %s", visible, boss_name)
        except discord.HTTPException as e:
            logger.error("Failed to update %s: %s", boss_name, e)
        except Exception:
            # An unhandled exception would stop the loop for good
            logger.exception("Unexpected error updating %s", boss_name)


async def setup(bot: Roberto):
    await bot.add_cog(Rotation(bot))
