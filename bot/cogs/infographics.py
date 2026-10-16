"""Yaphalla's infographic links and boss guides."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.channels import public_channel_id
from bot.core.checks import waiter_only
from bot.core.config import app_settings
from bot.ui.views import DropdownView

if TYPE_CHECKING:
    from bot.core.client import Roberto

MAX_AUTOCOMPLETE_CHOICES = 25


async def image_key_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=key, value=key)
        for key in app_settings.image_keys
        if key.lower().startswith(current.lower())
    ][:MAX_AUTOCOMPLETE_CHOICES]


class Infographics(commands.Cog):
    def __init__(self, bot: Roberto):
        self.bot = bot

    async def send_infographic(self, interaction: discord.Interaction, key: str, ephemeral: bool = False):
        """Reply with the stored infographic for a key."""
        infographic = await self.bot.infographic_service.get(key)
        if infographic is None:
            await interaction.response.send_message(f"No infographic has been set for `{key}` yet.", ephemeral=True)
            return
        await interaction.response.send_message(infographic, ephemeral=ephemeral)

    async def send_boss_dropdown(self, interaction: discord.Interaction, title: str, bosses: list[str]):
        """Reply with a game mode's boss channels and a dropdown of their infographics."""
        channel_ids = [public_channel_id(boss_name) for boss_name in bosses]
        text = "\n".join(f"<#{channel_id}>" for channel_id in channel_ids if channel_id)
        text += "\n\nView Boss Infographs by selecting a Boss below."

        embed = discord.Embed(
            title=f"S{app_settings.season} {title}",
            description=text,
            color=discord.Color.fuchsia(),
        )

        view = DropdownView(bosses, "Select a Boss...", self.send_infographic)
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @app_commands.command(name="paragon", description="Show Yaphalla's Paragon Graphic")
    async def paragon(self, interaction: discord.Interaction):
        await self.send_infographic(interaction, "paragon")

    @app_commands.command(name="charms", description="Show Yaphalla's DR Charms Graphic")
    async def charms(self, interaction: discord.Interaction):
        await self.send_infographic(interaction, "charms")

    @app_commands.command(name="dream-realm", description="Yaphalla's Dream Realm infographics")
    async def dream_realm(self, interaction: discord.Interaction):
        await self.send_boss_dropdown(interaction, "Dream Realm Bosses", app_settings.game_modes.dream_realm)

    @app_commands.command(name="dr", description="Yaphalla's Dream Realm infographics")
    async def dr(self, interaction: discord.Interaction):
        await self.send_boss_dropdown(interaction, "Dream Realm Bosses", app_settings.game_modes.dream_realm)

    @app_commands.command(name="primal-lord", description="Yaphalla's Primal Lord infographics")
    async def primal_lord(self, interaction: discord.Interaction):
        await self.send_boss_dropdown(interaction, "Primal Lords", app_settings.game_modes.primal_lords)

    @app_commands.command(name="pl", description="Yaphalla's Primal Lord infographics")
    async def pl(self, interaction: discord.Interaction):
        await self.send_boss_dropdown(interaction, "Primal Lords", app_settings.game_modes.primal_lords)

    @app_commands.command(name="ravaged-realm", description="Yaphalla's Ravaged Realm infographics")
    async def ravaged_realm(self, interaction: discord.Interaction):
        await self.send_boss_dropdown(interaction, "Ravaged Realm", app_settings.game_modes.ravaged_realm)

    @app_commands.command(name="yap_update_image", description="Update the infographic shown for a key")
    @app_commands.describe(key="Infographic to update", text="New text or image link; :yapName: becomes an emoji")
    @app_commands.autocomplete(key=image_key_autocomplete)
    @waiter_only()
    async def yap_update_image(self, interaction: discord.Interaction, key: str, text: str):
        if key not in app_settings.image_keys:
            await interaction.response.send_message("Invalid image key.", ephemeral=True)
            return

        infographic = await self.bot.infographic_service.set(key, text)
        await interaction.response.send_message(infographic)


async def setup(bot: Roberto):
    await bot.add_cog(Infographics(bot))
