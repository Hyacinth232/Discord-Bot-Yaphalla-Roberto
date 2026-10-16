from types import SimpleNamespace
from unittest.mock import MagicMock

import discord
import pytest

from bot.core.checks import is_stage_role, is_waiter
from bot.core.config import app_settings

WAITER_ROLE = app_settings.roles.waiter[0]
STAGE_ROLE = app_settings.roles.stage[0]


def member_interaction(interaction, role_ids=(), administrator=False, user_id=42, guild_id=app_settings.server_id):
    member = MagicMock(spec=discord.Member)
    member.id = user_id
    member.roles = [SimpleNamespace(id=role_id) for role_id in role_ids]
    member.guild_permissions = SimpleNamespace(administrator=administrator)
    interaction.user = member
    interaction.guild = SimpleNamespace(id=guild_id)
    return interaction


@pytest.mark.parametrize(
    ("kwargs", "waiter", "stage"),
    [
        ({"role_ids": [WAITER_ROLE]}, True, False),
        ({"role_ids": [STAGE_ROLE]}, False, True),
        ({"role_ids": []}, False, False),
        ({"administrator": True}, True, True),
        ({"user_id": app_settings.amaryllis_id}, True, True),
        ({"role_ids": [WAITER_ROLE], "guild_id": 1}, False, False),
    ],
)
def test_role_checks(interaction, kwargs: dict, waiter: bool, stage: bool):
    member_interaction(interaction, **kwargs)
    assert is_waiter(interaction) is waiter
    assert is_stage_role(interaction) is stage


def test_direct_messages_fail_checks(interaction):
    interaction.guild = None
    assert not is_waiter(interaction)
