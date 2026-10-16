"""Modals that collect submission details and hand them to a callback."""

import logging
from collections.abc import Awaitable, Callable

import discord

from bot.submission.submission import SheetDetails, StageDetails

logger = logging.getLogger(__name__)

ERROR_MESSAGE = "Something went wrong with your submission. Please try again or contact staff."


class _CallbackModal(discord.ui.Modal):
    """Defers the interaction, then passes the modal's parsed values to a callback."""

    def __init__(self, on_submit: Callable[[discord.Interaction, object], Awaitable[None]]):
        super().__init__()
        self._on_submit = on_submit

    def parse(self) -> object:
        """Return the value handed to the callback."""
        raise NotImplementedError

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self._on_submit(interaction, self.parse())

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error("Error handling %s", type(self).__name__, exc_info=error)
        if interaction.response.is_done():
            await interaction.followup.send(ERROR_MESSAGE, ephemeral=True)
        else:
            await interaction.response.send_message(ERROR_MESSAGE, ephemeral=True)


class EditTextModal(_CallbackModal, title="Edit and Submit Formation"):
    """Lets the submitter edit the message text before submitting."""

    edited_text = discord.ui.TextInput(label="Edit the text", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, on_submit: Callable[[discord.Interaction, str], Awaitable[None]], default_text: str):
        super().__init__(on_submit)
        self.edited_text.default = default_text

    def parse(self) -> str:
        return self.edited_text.value


class SheetDetailsModal(_CallbackModal, title="Submit Formation (by Take)"):
    """Collects the details recorded on the Dream Realm tracking sheet."""

    credits_field = discord.ui.TextInput(label="Credits", placeholder="(e.g. Frosty)", required=False, max_length=100)

    damage_field = discord.ui.TextInput(
        label="Damage", placeholder="(e.g. 37.1B or 17682M)", required=True, min_length=2, max_length=100
    )

    resonance_field = discord.ui.TextInput(
        label="Resonance level", placeholder="(e.g. 223-225 or 427)", required=False, min_length=2, max_length=10
    )

    ascension_field = discord.ui.TextInput(
        label="DPS Carry's ascension", placeholder="(e.g. M+ or P2)", required=True, min_length=1, max_length=10
    )

    notes_field = discord.ui.TextInput(
        label="Notes", style=discord.TextStyle.paragraph, required=False, min_length=1, max_length=1000
    )

    def parse(self) -> SheetDetails:
        return SheetDetails(
            credits=self.credits_field.value,
            damage=self.damage_field.value,
            resonance=self.resonance_field.value,
            ascension=self.ascension_field.value,
            notes=self.notes_field.value,
        )


class StageDetailsModal(_CallbackModal, title="Stage Submission"):
    """Collects the details of an AFK stage clear."""

    stage_field = discord.ui.TextInput(
        label="STAGE", placeholder="(e.g. S3, P45, SA392, PA979, etc.)", required=True, min_length=2, max_length=8
    )

    charms_gear_field = discord.ui.TextInput(
        label="Charms/Gear",
        style=discord.TextStyle.paragraph,
        placeholder="Enter charms and gear information...",
        required=False,
        max_length=1000,
    )

    timings_field = discord.ui.TextInput(
        label="Timings",
        style=discord.TextStyle.paragraph,
        placeholder="Enter timing information...",
        required=False,
        max_length=1000,
    )

    replays_field = discord.ui.TextInput(
        label="Replays",
        style=discord.TextStyle.paragraph,
        placeholder="Enter replay links or information...",
        required=False,
        max_length=1000,
    )

    notes_field = discord.ui.TextInput(
        label="Notes",
        style=discord.TextStyle.paragraph,
        placeholder="Enter your notes here...",
        required=False,
        max_length=1000,
    )

    def parse(self) -> StageDetails:
        return StageDetails(
            stage=self.stage_field.value.upper(),
            charms_gear=self.charms_gear_field.value,
            timings=self.timings_field.value,
            replays=self.replays_field.value,
            notes=self.notes_field.value,
        )
