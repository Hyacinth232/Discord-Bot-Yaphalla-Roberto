import re
from datetime import datetime, timezone

import discord

from bot.core.constants import (ALIAS_DICT, EMOJIS, PRIVATE_CHANNEL_IDS,
                                PUBLIC_CHANNEL_IDS, ROBERTO_ID, RR_BOSSES)
from bot.core.enum_classes import BossType, ChannelType


def sanitize_user_input(value: str) -> str:
    if isinstance(value, str) and value.startswith(("=", "+", "-")):
        return "'" + value
    return value

pub_dict = {id: name for name, id in PUBLIC_CHANNEL_IDS.items()}
priv_dict = {id: name for name, id in PRIVATE_CHANNEL_IDS.items()}

def is_kitchen_channel(id: int) -> bool:
    return id in pub_dict or id in priv_dict

def _is_ravaged_realm_channel(id: int) -> bool:
    if id in pub_dict:
        return pub_dict[id] in RR_BOSSES
    if id in priv_dict:
        return priv_dict[id] in RR_BOSSES
    return False

def is_afk_channel(id: int) -> bool:
    return id == PUBLIC_CHANNEL_IDS["AFK"]

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
    
    return bot_id or ROBERTO_ID

def _to_pub_id(id: int, boss_type: BossType) -> int | None:
    if boss_type == BossType.NORMAL:
        return PUBLIC_CHANNEL_IDS["AFK"]
    if boss_type == BossType.PHANTIMAL:
        return PUBLIC_CHANNEL_IDS["AFK"]
    
    if id in pub_dict:
        return id
    if id in priv_dict:
        return PUBLIC_CHANNEL_IDS[priv_dict[id]]
    return None

def _to_priv_id(id: int, boss_type: BossType) -> int | None:
    if boss_type == BossType.NORMAL:
        return PRIVATE_CHANNEL_IDS["Normal"]
    if boss_type == BossType.PHANTIMAL:
        return PRIVATE_CHANNEL_IDS["Phantimal"]
    
    if id in priv_dict:
        return id
    if id in pub_dict:
        return PRIVATE_CHANNEL_IDS[pub_dict[id]]
    return None

def to_channel_type_id(channel_type: ChannelType, channel_id: int, boss_type: BossType=BossType.DREAM_REALM):
    if channel_type == ChannelType.PUBLIC:
        return _to_pub_id(channel_id, boss_type)
    
    if channel_type == ChannelType.PRIVATE:
        return _to_priv_id(channel_id, boss_type)
    return None

def get_emoji(name: str):
    emoji_name = name.replace('-', '').replace('&', '')
    return '<:{}:{}>'.format(emoji_name, str(EMOJIS.get(emoji_name, name)))

def replace_emojis(text):
    pattern = r':([a-zA-Z0-9_]+):'

    def replacer(match):
        yap_name = match.group(1)
        emoji_name = yap_name.removeprefix('yap')
        return get_emoji(emoji_name)

    return re.sub(pattern, replacer, text)

def split_input(input: str) -> list[str]:
    return [text for text in re.split(r'[，,、\s]+', input) if text]

def translate_name(name: str, alias_dict: dict=ALIAS_DICT):
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


async def get_or_fetch_guild(bot: discord.Client, guild_id: int) -> discord.Guild | None:
    """Get guild from cache, or fetch if not found."""
    guild = bot.get_guild(guild_id)
    if not guild:
        guild = await bot.fetch_guild(guild_id)
    return guild


async def get_or_fetch_channel(guild: discord.Guild, channel_id: int) -> discord.abc.GuildChannel | discord.Thread | None:
    """Get channel from cache, or fetch if not found."""
    channel = guild.get_channel(channel_id)
    if not channel:
        channel = await guild.fetch_channel(channel_id)
    return channel


async def get_or_fetch_member(guild: discord.Guild, member_id: int) -> discord.Member | None:
    """Get member from cache, or fetch if not found."""
    member = guild.get_member(member_id)
    if not member:
        member = await guild.fetch_member(member_id)
    return member