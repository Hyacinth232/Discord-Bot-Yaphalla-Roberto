"""Role pings for kitchen staff."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.channels import is_public_kitchen_channel
from bot.core.checks import waiter_only
from bot.core.config import app_settings

if TYPE_CHECKING:
    from bot.core.client import Roberto

# Leaves room in Discord's 2000 character limit for the role mention
MAX_MESSAGE_LENGTH = 1900
ROLE_PINGS = discord.AllowedMentions(everyone=False, users=False, roles=True)


class Staff(commands.Cog):
    def __init__(self, bot: Roberto):
        self.bot = bot

    @app_commands.command(name="benchmark", description="Ping the benchmark team")
    @waiter_only()
    async def benchmark(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"<@&{app_settings.roles.benchmark}>", allowed_mentions=ROLE_PINGS)

    @app_commands.command(name="souschef", description="Ping the sous chefs with a message")
    @app_commands.describe(message="Message to send with the ping")
    @waiter_only()
    async def souschef(
        self,
        interaction: discord.Interaction,
        message: app_commands.Range[str, 1, MAX_MESSAGE_LENGTH],
        file1: discord.Attachment = None,
        file2: discord.Attachment = None,
        file3: discord.Attachment = None,
    ):
        channel_id = interaction.channel_id
        if not is_public_kitchen_channel(channel_id) and channel_id not in app_settings.souschef_extra_channel_ids:
            await interaction.response.send_message(
                "This command can only be used in Kitchen channels.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        files = [await file.to_file() for file in (file1, file2, file3) if file is not None]
        await interaction.followup.send(
            f"<@&{app_settings.roles.souschef}> {message}", files=files, allowed_mentions=ROLE_PINGS
        )


async def setup(bot: Roberto):
    await bot.add_cog(Staff(bot))
