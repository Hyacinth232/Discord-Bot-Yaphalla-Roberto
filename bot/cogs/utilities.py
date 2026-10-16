"""General-purpose tools: Discord timestamps and WebP conversion."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from PIL import UnidentifiedImageError

from bot.core.utils import datetime_now, discord_timestamp
from bot.image.webp_converter import DEFAULT_QUALITY, MAX_QUALITY, MIN_QUALITY, convert_to_webp

if TYPE_CHECKING:
    from bot.core.client import Roberto


def _is_image(attachment: discord.Attachment) -> bool:
    return (attachment.content_type or "").startswith("image/")


def _first_image(message: discord.Message) -> discord.Attachment | None:
    """First image attached to a message, looking inside forwarded messages too."""
    source = message.message_snapshots[0] if message.flags.forwarded and message.message_snapshots else message
    return next((attachment for attachment in source.attachments if _is_image(attachment)), None)


class Utilities(commands.Cog):
    def __init__(self, bot: Roberto):
        self.bot = bot
        self.context_menus = [
            app_commands.ContextMenu(name="Convert to WebP", callback=self.convert_message_to_webp),
            app_commands.ContextMenu(name="Convert to Lossless WebP", callback=self.convert_message_to_lossless_webp),
        ]

    async def cog_load(self):
        for menu in self.context_menus:
            self.bot.tree.add_command(menu)

    async def cog_unload(self):
        for menu in self.context_menus:
            self.bot.tree.remove_command(menu.name, type=menu.type)

    ### TIMESTAMPS
    @app_commands.command(name="get_timestamp", description="Convert a date/time to a UTC Discord timestamp")
    @app_commands.describe(year="Defaults to the current year", hour="Hour in UTC (0-23)")
    async def get_timestamp(
        self,
        interaction: discord.Interaction,
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31],
        year: int | None = None,
        hour: app_commands.Range[int, 0, 23] = 0,
    ):
        try:
            dt = datetime(year or datetime_now().year, month, day, hour, tzinfo=UTC)
        except ValueError as e:
            await interaction.response.send_message(f"Invalid date: {e}", ephemeral=True)
            return
        await interaction.response.send_message(discord_timestamp(dt))

    @app_commands.command(name="time_now", description="Show the current time as a Discord timestamp")
    async def time_now(self, interaction: discord.Interaction):
        await interaction.response.send_message(discord_timestamp(datetime_now()))

    ### WEBP
    @app_commands.command(name="webp", description="Convert an image to WebP")
    @app_commands.describe(
        image="Image to convert",
        quality=f"Compression quality, {MIN_QUALITY}-{MAX_QUALITY} (default {DEFAULT_QUALITY}); ignored when lossless",
        lossless="Use lossless compression",
    )
    async def webp(
        self,
        interaction: discord.Interaction,
        image: discord.Attachment,
        quality: app_commands.Range[int, MIN_QUALITY, MAX_QUALITY] = DEFAULT_QUALITY,
        lossless: bool = False,
    ):
        await self._send_webp(interaction, image, quality, lossless)

    async def convert_message_to_webp(self, interaction: discord.Interaction, message: discord.Message):
        await self._send_webp(interaction, _first_image(message), DEFAULT_QUALITY, lossless=False)

    async def convert_message_to_lossless_webp(self, interaction: discord.Interaction, message: discord.Message):
        await self._send_webp(interaction, _first_image(message), MAX_QUALITY, lossless=True)

    async def _send_webp(
        self, interaction: discord.Interaction, attachment: discord.Attachment | None, quality: int, lossless: bool
    ):
        """Convert an image and post it with a copyable link to the converted file."""
        if attachment is None or not _is_image(attachment):
            await interaction.response.send_message("Please choose an image.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        image_bytes = await attachment.read()
        try:
            buffer, filename = await asyncio.to_thread(
                convert_to_webp, image_bytes, attachment.filename, quality, lossless
            )
        except UnidentifiedImageError, OSError:
            await interaction.followup.send(f"Couldn't read `{attachment.filename}` as an image.")
            return

        text = discord_timestamp(datetime_now())
        sent = await interaction.followup.send(text, file=discord.File(fp=buffer, filename=filename), wait=True)
        if sent.attachments:
            await sent.edit(content=f"```{text}\n{sent.attachments[0].url}```")


async def setup(bot: Roberto):
    await bot.add_cog(Utilities(bot))
