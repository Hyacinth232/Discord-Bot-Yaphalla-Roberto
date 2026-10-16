import contextlib
from collections.abc import Awaitable, Callable

import discord

from bot.core.config import app_settings


class Dropdown(discord.ui.Select):
    """Dropdown select menu for boss selection."""

    def __init__(
        self,
        options: list[str],
        placeholder: str,
        callback_func: Callable[[discord.Interaction, str, bool], Awaitable[None]],
    ):
        """Initialize dropdown with options and callback."""
        self.callback_func = callback_func
        options = [discord.SelectOption(label=key) for key in options]
        super().__init__(placeholder=placeholder, options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection."""
        ephemeral = interaction.user.id != app_settings.amaryllis_id
        await self.callback_func(interaction, self.values[0], ephemeral)


class DropdownView(discord.ui.View):
    """View containing a dropdown select menu."""

    def __init__(
        self,
        options: list[str],
        placeholder: str,
        callback_func: Callable[[discord.Interaction, str, bool], Awaitable[None]],
    ):
        """Initialize view with dropdown."""
        super().__init__(timeout=300)
        self.dropdown = Dropdown(options, placeholder, callback_func)
        self.add_item(self.dropdown)
        self.message: discord.Message | None = None

    async def on_timeout(self):
        """Disable dropdown when view times out."""
        for item in self.children:
            item.disabled = True

        if self.message:
            with contextlib.suppress(discord.NotFound):
                await self.message.edit(view=self)
