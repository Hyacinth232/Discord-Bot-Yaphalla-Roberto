import logging
import re
from datetime import datetime, timezone

import discord

from bot.core.config import app_settings, data_settings
from bot.core.enum_classes import BossType, ChannelType

logger = logging.getLogger()


async def get_or_fetch_server(bot: discord.Client, server_id: int) -> discord.Guild | None:
    """Get server from cache, or fetch if not found."""
    server = bot.get_guild(server_id)
    if not server:
        try:
            server = await bot.fetch_guild(server_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error("Failed to fetch server {}: {}".format(server_id, e))
            return None
    return server


async def get_or_fetch_channel(server: discord.Guild, chan_id: int) -> discord.abc.GuildChannel | discord.Thread | None:
    """Get channel from cache, or fetch if not found."""
    channel = server.get_channel(chan_id)
    if not channel:
        try:
            channel = await server.fetch_channel(chan_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error("Failed to fetch channel {}: {}".format(chan_id, e))
            return None
    return channel


async def get_or_fetch_member(server: discord.Guild, member_id: int) -> discord.Member | None:
    """Get member from cache, or fetch if not found."""
    member = server.get_member(member_id)
    if not member:
        try:
            member = await server.fetch_member(member_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error("Failed to fetch member {}: {}".format(member_id, e))
            return None
    return member


def sanitize_user_input(value: str) -> str:
    if isinstance(value, str) and value.startswith(("=", "+", "-")):
        return "'" + value
    return value

pub_dict = {id: name for name, id in app_settings.public_channel_names_to_ids.items()}
priv_dict = {id: name for name, id in app_settings.private_channel_names_to_ids.items()}

def is_kitchen_channel(id: int) -> bool:
    return id in pub_dict or id in priv_dict

def _is_ravaged_realm_channel(id: int) -> bool:
    if id in pub_dict:
        return pub_dict[id] in app_settings.ravaged_realm
    if id in priv_dict:
        return priv_dict[id] in app_settings.ravaged_realm
    return False

def is_afk_channel(id: int) -> bool:
    return id == app_settings.public_channel_names_to_ids["AFK"] or id == app_settings.private_channel_names_to_ids["Normal"] or id == app_settings.private_channel_names_to_ids["Phantimal"]

def to_channel_name(id: int) -> str | None:
    if id in pub_dict:
        return pub_dict[id]
    if id in priv_dict:
        return priv_dict[id]
    return None

def to_bot_id(id: int, boss_type: BossType) -> int:
    bot_id = None
    
    if boss_type == BossType.NORMAL or boss_type == BossType.PHANTIMAL:
        bot_id = _to_priv_id(id, boss_type)
    
    bot_id = bot_id or _to_pub_id(id, boss_type)
    
    return bot_id or app_settings.roberto_id

def _to_pub_id(id: int, boss_type: BossType) -> int | None:
    if boss_type == BossType.NORMAL:
        return app_settings.public_channel_names_to_ids["AFK"]
    if boss_type == BossType.PHANTIMAL:
        return app_settings.public_channel_names_to_ids["AFK"]
    
    if id in pub_dict:
        return id
    if id in priv_dict:
        return app_settings.public_channel_names_to_ids[priv_dict[id]]
    return None

def _to_priv_id(id: int, boss_type: BossType) -> int | None:
    if boss_type == BossType.NORMAL:
        return app_settings.private_channel_names_to_ids["Normal"]
    if boss_type == BossType.PHANTIMAL:
        return app_settings.private_channel_names_to_ids["Phantimal"]
    
    if id in priv_dict:
        return id
    if id in pub_dict:
        return app_settings.private_channel_names_to_ids[pub_dict[id]]
    return None

def to_channel_type_id(channel_type: ChannelType, channel_id: int, boss_type: BossType=BossType.DREAM_REALM):
    if channel_type == ChannelType.PUBLIC:
        return _to_pub_id(channel_id, boss_type)
    
    if channel_type == ChannelType.PRIVATE:
        return _to_priv_id(channel_id, boss_type)
    return None

def get_emoji(name: str):
    emoji_name = name.replace('-', '').replace('&', '')
    return '<:{}:{}>'.format(emoji_name, str(data_settings.emojis.get(emoji_name, name)))

def replace_emojis(text):
    pattern = r':([a-zA-Z0-9_]+):'

    def replacer(match):
        yap_name = match.group(1)
        emoji_name = yap_name.removeprefix('yap')
        return get_emoji(emoji_name)

    return re.sub(pattern, replacer, text)

def split_input(input: str) -> list[str]:
    return [text for text in re.split(r'[，,、\s]+', input) if text]

def translate_name(name: str, alias_dict: dict | None = None):
    if alias_dict is None:
        alias_dict = data_settings.alias_dict
    name = name.title()
    if name in alias_dict:
        name = alias_dict[name]
    return name

def clean_input_str(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9 ?!\'\-\(\):,]', '', text)
    #text = text.title()
    return text

def discord_timestamp(dt: datetime) -> str:
    unix_timestamp = int(dt.timestamp())
    return "<t:{}:f>".format(unix_timestamp)

def datetime_now() -> datetime:
    return datetime.now(timezone.utc)