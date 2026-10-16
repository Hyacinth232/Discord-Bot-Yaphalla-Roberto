import pytest

from bot.core.channels import (
    is_afk_channel,
    is_kitchen_channel,
    is_public_kitchen_channel,
    to_channel_name,
    to_channel_type_id,
)
from bot.core.config import app_settings
from bot.core.enum_classes import BossType, ChannelType

KING_CROAKER = app_settings.bosses["King Croaker"]
AFK = app_settings.afk


@pytest.mark.parametrize(
    ("channel_id", "name"),
    [
        (KING_CROAKER.public, "King Croaker"),
        (KING_CROAKER.private, "King Croaker"),
        # These names key the submission counters and sheet tabs, so they must stay stable
        (AFK.public, "AFK"),
        (AFK.normal, "Normal"),
        (AFK.phantimal, "Phantimal"),
        (1, None),
    ],
)
def test_channel_names(channel_id: int, name: str | None):
    assert to_channel_name(channel_id) == name


def test_channel_kinds():
    assert is_kitchen_channel(KING_CROAKER.private)
    assert is_public_kitchen_channel(KING_CROAKER.public)
    assert not is_public_kitchen_channel(KING_CROAKER.private)
    assert all(is_afk_channel(channel_id) for channel_id in (AFK.public, AFK.normal, AFK.phantimal))
    assert not is_afk_channel(KING_CROAKER.public)
    assert not is_kitchen_channel(1)


@pytest.mark.parametrize(
    ("channel_type", "channel_id", "boss_type", "expected"),
    [
        (ChannelType.PRIVATE, KING_CROAKER.public, BossType.DREAM_REALM, KING_CROAKER.private),
        (ChannelType.PRIVATE, KING_CROAKER.private, BossType.DREAM_REALM, KING_CROAKER.private),
        (ChannelType.PUBLIC, KING_CROAKER.private, BossType.DREAM_REALM, KING_CROAKER.public),
        (ChannelType.PRIVATE, AFK.public, BossType.NORMAL, AFK.normal),
        (ChannelType.PRIVATE, AFK.public, BossType.PHANTIMAL, AFK.phantimal),
        (ChannelType.PUBLIC, AFK.normal, BossType.NORMAL, AFK.public),
        (ChannelType.PRIVATE, 1, BossType.DREAM_REALM, None),
    ],
)
def test_forwarding_targets(channel_type: ChannelType, channel_id: int, boss_type: BossType, expected: int | None):
    assert to_channel_type_id(channel_type, channel_id, boss_type) == expected
