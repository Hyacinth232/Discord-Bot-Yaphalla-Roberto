"""Mapping between kitchen channels and the public/private channels submissions are forwarded to."""

from bot.core.config import app_settings
from bot.core.enum_classes import BossType, ChannelType

# Channel names double as submission counter keys and sheet names, so these must not change
AFK_NAME = "AFK"
NORMAL_NAME = "Normal"
PHANTIMAL_NAME = "Phantimal"

_afk = app_settings.afk
_public_names = {channels.public: name for name, channels in app_settings.bosses.items()} | {_afk.public: AFK_NAME}
_private_names = {channels.private: name for name, channels in app_settings.bosses.items()} | {
    _afk.normal: NORMAL_NAME,
    _afk.phantimal: PHANTIMAL_NAME,
}
_AFK_CHANNEL_IDS = {_afk.public, _afk.normal, _afk.phantimal}


def is_kitchen_channel(channel_id: int) -> bool:
    return channel_id in _public_names or channel_id in _private_names


def is_public_kitchen_channel(channel_id: int) -> bool:
    return channel_id in _public_names


def is_afk_channel(channel_id: int) -> bool:
    return channel_id in _AFK_CHANNEL_IDS


def to_channel_name(channel_id: int) -> str | None:
    return _public_names.get(channel_id) or _private_names.get(channel_id)


def public_channel_id(boss_name: str) -> int | None:
    channels = app_settings.bosses.get(boss_name)
    return channels.public if channels else None


def _to_public_id(channel_id: int, boss_type: BossType) -> int | None:
    if boss_type in (BossType.NORMAL, BossType.PHANTIMAL):
        return _afk.public

    if channel_id in _public_names:
        return channel_id
    if channel_id in _private_names:
        return public_channel_id(_private_names[channel_id])
    return None


def _to_private_id(channel_id: int, boss_type: BossType) -> int | None:
    if boss_type == BossType.NORMAL:
        return _afk.normal
    if boss_type == BossType.PHANTIMAL:
        return _afk.phantimal

    if channel_id in _private_names:
        return channel_id
    if channel_id in _public_names:
        channels = app_settings.bosses.get(_public_names[channel_id])
        return channels.private if channels else None
    return None


def to_channel_type_id(
    channel_type: ChannelType, channel_id: int, boss_type: BossType = BossType.DREAM_REALM
) -> int | None:
    """Resolve the public or private channel a kitchen channel's submissions go to."""
    if channel_type == ChannelType.PUBLIC:
        return _to_public_id(channel_id, boss_type)
    return _to_private_id(channel_id, boss_type)
