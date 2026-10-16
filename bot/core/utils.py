import logging
import re
from datetime import UTC, datetime

import discord

from bot.core.config import data_settings

logger = logging.getLogger(__name__)


async def get_or_fetch_server(bot: discord.Client, server_id: int) -> discord.Guild | None:
    """Get server from cache, or fetch if not found."""
    server = bot.get_guild(server_id)
    if not server:
        try:
            server = await bot.fetch_guild(server_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error("Failed to fetch server %s: %s", server_id, e)
            return None
    return server


async def get_or_fetch_channel(server: discord.Guild, chan_id: int) -> discord.abc.GuildChannel | discord.Thread | None:
    """Get channel from cache, or fetch if not found."""
    channel = server.get_channel(chan_id)
    if not channel:
        try:
            channel = await server.fetch_channel(chan_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error("Failed to fetch channel %s: %s", chan_id, e)
            return None
    return channel


async def get_or_fetch_member(server: discord.Guild, member_id: int) -> discord.Member | None:
    """Get member from cache, or fetch if not found."""
    member = server.get_member(member_id)
    if not member:
        try:
            member = await server.fetch_member(member_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error("Failed to fetch member %s: %s", member_id, e)
            return None
    return member


def sanitize_user_input(value: str) -> str:
    """Stop spreadsheet cells from being interpreted as formulas."""
    if isinstance(value, str) and value.startswith(("=", "+", "-")):
        return "'" + value
    return value


def get_emoji(name: str) -> str:
    emoji_name = name.replace("-", "").replace("&", "")
    return f"<:{emoji_name}:{data_settings.emojis.get(emoji_name, name)!s}>"


def replace_emojis(text: str) -> str:
    """Replace :yapName: placeholders with the server's custom emojis."""
    pattern = r":([a-zA-Z0-9_]+):"

    def replacer(match):
        yap_name = match.group(1)
        emoji_name = yap_name.removeprefix("yap")
        return get_emoji(emoji_name)

    return re.sub(pattern, replacer, text)


def discord_timestamp(dt: datetime) -> str:
    unix_timestamp = int(dt.timestamp())
    return f"<t:{unix_timestamp}:f>"


def datetime_now() -> datetime:
    return datetime.now(UTC)
