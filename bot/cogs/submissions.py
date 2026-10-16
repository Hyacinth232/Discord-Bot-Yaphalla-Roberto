"""Submitting teams and stages from the kitchen channels."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.channels import is_afk_channel, is_kitchen_channel
from bot.core.checks import stage_role_only
from bot.core.enum_classes import BossType, ChannelType
from bot.submission.submission import SheetDetails, StageDetails, Submission
from bot.ui.modals import EditTextModal, SheetDetailsModal, StageDetailsModal

if TYPE_CHECKING:
    from bot.core.client import Roberto

THANK_YOU = "Thank you for the submission!"
STAGE_THANK_YOU = "Stage submission received! Thank you for your submission."


def _team_channel_error(channel: discord.abc.Messageable | None) -> str | None:
    """Return why team submissions aren't allowed from this channel, or None if they are."""
    if channel is None or isinstance(channel, (discord.DMChannel, discord.GroupChannel)):
        return "Submissions are only allowed from Yaphalla."
    if not is_kitchen_channel(channel.id):
        return "Submissions are only allowed from Kitchen channels."
    if is_afk_channel(channel.id):
        return "Use `/submit_normal` or `/submit_phantimal` for the AFK channel."
    return None


class Submissions(commands.Cog):
    def __init__(self, bot: Roberto):
        self.bot = bot
        self.context_menus = [
            app_commands.ContextMenu(name="Submit Team", callback=self.submit_team),
            app_commands.ContextMenu(name="Edit & Submit Team", callback=self.edit_and_submit_team),
            app_commands.ContextMenu(name="Submit Team w/ Details", callback=self.submit_team_with_details),
        ]

    async def cog_load(self):
        for menu in self.context_menus:
            self.bot.tree.add_command(menu)

    async def cog_unload(self):
        for menu in self.context_menus:
            self.bot.tree.remove_command(menu.name, type=menu.type)

    def _submission(self, interaction: discord.Interaction, channel_id: int, **kwargs) -> Submission:
        return Submission(self.bot, self.bot.counter_service, interaction.user, channel_id, **kwargs)

    async def _process(
        self,
        interaction: discord.Interaction,
        submission: Submission,
        *,
        post_public: bool = False,
        acknowledgement: str = THANK_YOU,
    ):
        """Forward a submission and export it to the sheet. The interaction must already be deferred."""
        await submission.register()

        public_link = None
        if post_public:
            public_message = await submission.forward(ChannelType.PUBLIC)
            public_link = public_message.jump_url if public_message else None

        await interaction.followup.send(acknowledgement, ephemeral=True)
        await submission.forward(ChannelType.PRIVATE, public_link=public_link)
        await submission.export_to_sheet(public_link)

    ### CONTEXT MENUS
    async def submit_team(self, interaction: discord.Interaction, message: discord.Message):
        """Submit a message as-is."""
        if error := _team_channel_error(message.channel):
            await interaction.response.send_message(error, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        await self._process(interaction, self._submission(interaction, message.channel.id, message=message))

    async def edit_and_submit_team(self, interaction: discord.Interaction, message: discord.Message):
        """Submit a message after editing its text."""
        if error := _team_channel_error(message.channel):
            await interaction.response.send_message(error, ephemeral=True)
            return

        async def on_submit(modal_interaction: discord.Interaction, text: str):
            submission = self._submission(modal_interaction, message.channel.id, message=message, content=text)
            await self._process(modal_interaction, submission)

        source = message.message_snapshots[0] if message.flags.forwarded and message.message_snapshots else message
        await interaction.response.send_modal(EditTextModal(on_submit, default_text=source.content))

    async def submit_team_with_details(self, interaction: discord.Interaction, message: discord.Message):
        """Submit a message along with details for the tracking sheet."""
        if error := _team_channel_error(message.channel):
            await interaction.response.send_message(error, ephemeral=True)
            return

        async def on_submit(modal_interaction: discord.Interaction, details: SheetDetails):
            submission = self._submission(modal_interaction, message.channel.id, message=message, sheet_details=details)
            await self._process(modal_interaction, submission)

        await interaction.response.send_modal(SheetDetailsModal(on_submit))

    ### SLASH COMMANDS
    @app_commands.command(name="submit", description="Submit a team with details for the tracking sheet")
    async def submit(
        self,
        interaction: discord.Interaction,
        file1: discord.Attachment,
        file2: discord.Attachment = None,
        file3: discord.Attachment = None,
        file4: discord.Attachment = None,
        file5: discord.Attachment = None,
    ):
        if error := _team_channel_error(interaction.channel):
            await interaction.response.send_message(error, ephemeral=True)
            return

        attachments = [file for file in (file1, file2, file3, file4, file5) if file is not None]
        channel_id = interaction.channel.id

        async def on_submit(modal_interaction: discord.Interaction, details: SheetDetails):
            submission = self._submission(modal_interaction, channel_id, attachments=attachments, sheet_details=details)
            await self._process(modal_interaction, submission, post_public=True)

        await interaction.response.send_modal(SheetDetailsModal(on_submit))

    @app_commands.command(name="submit_normal", description="Submit a stage to normal")
    @stage_role_only()
    async def submit_normal(
        self,
        interaction: discord.Interaction,
        file1: discord.Attachment = None,
        file2: discord.Attachment = None,
        file3: discord.Attachment = None,
        file4: discord.Attachment = None,
        file5: discord.Attachment = None,
    ):
        await self._submit_stage(interaction, [file1, file2, file3, file4, file5], BossType.NORMAL)

    @app_commands.command(name="submit_phantimal", description="Submit a stage to phantimal")
    @stage_role_only()
    async def submit_phantimal(
        self,
        interaction: discord.Interaction,
        file1: discord.Attachment = None,
        file2: discord.Attachment = None,
        file3: discord.Attachment = None,
        file4: discord.Attachment = None,
        file5: discord.Attachment = None,
    ):
        await self._submit_stage(interaction, [file1, file2, file3, file4, file5], BossType.PHANTIMAL)

    async def _submit_stage(
        self, interaction: discord.Interaction, files: list[discord.Attachment | None], boss_type: BossType
    ):
        if interaction.channel is None or not is_afk_channel(interaction.channel.id):
            await interaction.response.send_message("This command can only be used in the AFK channel.", ephemeral=True)
            return

        attachments = [file for file in files if file is not None]
        channel_id = interaction.channel.id

        async def on_submit(modal_interaction: discord.Interaction, details: StageDetails):
            submission = self._submission(
                modal_interaction, channel_id, attachments=attachments, boss_type=boss_type, stage_details=details
            )
            await self._process(modal_interaction, submission, acknowledgement=STAGE_THANK_YOU)

        await interaction.response.send_modal(StageDetailsModal(on_submit))


async def setup(bot: Roberto):
    await bot.add_cog(Submissions(bot))
