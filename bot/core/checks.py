"""Permission checks for application commands."""

from collections.abc import Iterable

import discord
from discord import app_commands

from bot.core.config import app_settings


def _has_any_role(interaction: discord.Interaction, role_ids: Iterable[int]) -> bool:
    """Admins and Amaryllis always pass; otherwise the member needs one of the roles."""
    if interaction.guild is None or interaction.guild.id != app_settings.server_id:
        return False

    member = interaction.user
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator or member.id == app_settings.amaryllis_id:
        return True
    return any(role.id in role_ids for role in member.roles)


def is_waiter(interaction: discord.Interaction) -> bool:
    return _has_any_role(interaction, app_settings.roles.waiter)


def is_stage_role(interaction: discord.Interaction) -> bool:
    return _has_any_role(interaction, app_settings.roles.stage)


def waiter_only():
    return app_commands.check(is_waiter)


def stage_role_only():
    return app_commands.check(is_stage_role)
