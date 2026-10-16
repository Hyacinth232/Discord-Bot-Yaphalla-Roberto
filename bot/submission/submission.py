"""Forwarding kitchen submissions to the 📌 channels and the tracking sheet."""

import logging
from dataclasses import dataclass
from pathlib import Path

import discord

from bot.core.channels import to_channel_name, to_channel_type_id
from bot.core.config import app_settings
from bot.core.enum_classes import BossType, ChannelType
from bot.core.utils import get_or_fetch_channel, get_or_fetch_member, get_or_fetch_server
from bot.services.counter_service import CounterService
from bot.submission.google_sheets import add_row
from bot.ui.embeds import make_embeds

logger = logging.getLogger(__name__)

MAX_FILES_PER_MESSAGE = 10
SUBMITTED_REACTION = "📝"


@dataclass(frozen=True)
class SheetDetails:
    """Details collected for the Dream Realm tracking sheet."""

    credits: str
    damage: str
    resonance: str
    ascension: str
    notes: str


@dataclass(frozen=True)
class StageDetails:
    """Details collected for an AFK stage submission."""

    stage: str
    charms_gear: str
    timings: str
    replays: str
    notes: str


def _is_media(attachment: discord.Attachment) -> bool:
    content_type = attachment.content_type or ""
    return content_type.startswith(("image/", "video/"))


class Submission:
    """A single submission: either an existing message or attachments uploaded with a command."""

    def __init__(
        self,
        bot: discord.Client,
        counter_service: CounterService,
        submitter: discord.abc.User,
        channel_id: int,
        *,
        message: discord.Message = None,
        attachments: list[discord.Attachment] | None = None,
        content: str | None = None,
        boss_type: BossType = BossType.DREAM_REALM,
        sheet_details: SheetDetails = None,
        stage_details: StageDetails = None,
    ):
        """
        Args:
            submitter: The user running the command
            channel_id: Kitchen channel the submission came from
            message: Message being submitted (context menus); its attachments and content are used
            attachments: Files uploaded with a slash command, used when there is no message
            content: Replaces the message's text when given (e.g. edited in a modal)
        """
        self.bot = bot
        self.counter_service = counter_service
        self.submitter = submitter
        self.channel_id = channel_id
        self.message = message
        self.boss_type = boss_type
        self.sheet_details = sheet_details
        self.stage_details = stage_details

        source = None
        if message is not None:
            # Forwarded messages keep their content and files in a snapshot
            source = message.message_snapshots[0] if message.flags.forwarded and message.message_snapshots else message
            attachments = source.attachments

        self.content = content if content is not None else (source.content if source else "")
        self.attachments = [attachment for attachment in attachments or [] if _is_media(attachment)]

        self.boss_name = to_channel_name(channel_id)
        self.submission_id: int | None = None
        self.author_name = ""
        self.submitter_name = ""

    @property
    def link(self) -> str | None:
        """Jump link to the submitted message, if there is one."""
        return self.message.jump_url if self.message else None

    async def register(self):
        """Assign a submission ID, resolve display names and mark the original message."""
        guild = await get_or_fetch_server(self.bot, app_settings.server_id)
        author_id = self.message.author.id if self.message else self.submitter.id
        self.author_name = await self._display_name(guild, author_id)
        self.submitter_name = await self._display_name(guild, self.submitter.id)

        self.submission_id = await self.counter_service.increment(self.boss_name)

        if self.message:
            try:
                await self.message.add_reaction(SUBMITTED_REACTION)
            except discord.HTTPException as e:
                logger.warning("Could not react to submission %s: %s", self.message.jump_url, e)

    async def forward(self, channel_type: ChannelType, public_link: str | None = None) -> discord.Message | None:
        """Post the submission to its public or private channel and return the sent message."""
        guild = await get_or_fetch_server(self.bot, app_settings.server_id)
        channel_id = to_channel_type_id(channel_type, self.channel_id, self.boss_type)
        channel = await get_or_fetch_channel(guild, channel_id) if guild and channel_id else None
        if channel is None:
            logger.error("No %s channel to forward submission from channel %s", channel_type.name, self.channel_id)
            return None

        files = [
            await attachment.to_file(filename=f"img_{i}{Path(attachment.filename).suffix}")
            for i, attachment in enumerate(self.attachments[:MAX_FILES_PER_MESSAGE])
        ]
        footer = f"ID: {self.submission_id} | Submitted by: {self.submitter_name}"
        embeds = make_embeds(self.describe(public_link), footer, files)
        return await channel.send(embeds=embeds, files=files)

    async def export_to_sheet(self, public_link: str | None = None):
        """Add the submission to the tracking sheet, if sheet details were collected."""
        if self.sheet_details is None:
            return
        if not app_settings.spreadsheet_id:
            logger.info("No spreadsheet_id configured; skipping sheet export for submission %s", self.submission_id)
            return

        details = self.sheet_details
        await add_row(
            self.bot,
            self.submission_id,
            self.boss_name,
            self.author_name,
            details.resonance,
            details.ascension,
            self.link or public_link or "No URL",
            details.credits,
            details.damage,
            details.notes,
        )

    def describe(self, public_link: str | None = None) -> str:
        """Build the embed text for a forwarded submission."""
        title = self.stage_details.stage if self.stage_details else "Submission"
        lines = [f"## {title}"]

        link = self.link or public_link
        if link:
            lines.append(f"**Link:** {link}")
        lines.append(f"**From:** {self.author_name}")

        if self.sheet_details:
            details = self.sheet_details
            lines.append(f"**Credits:** {details.credits}")
            lines.append(f"**Damage:** {details.damage}")
            lines.append(f"**Ascension:** {details.ascension}")
            lines.append(f"**Resonance:** {details.resonance}")

        if self.stage_details:
            details = self.stage_details
            lines.append(f"**Charms/Gear:** {details.charms_gear}")
            lines.append(f"**Timings:** {details.timings}")
            lines.append(f"**Replays:** {details.replays}")
            lines.append(f"**Notes:** {details.notes}")

        text = "\n".join(lines) + "\n\n"

        if self.sheet_details and self.sheet_details.notes:
            text += self.sheet_details.notes + "\n\n"
        if self.content:
            text += self.content + "\n\n"
        if self.sheet_details:
            text += "-# Data exported to tracking sheet! ✅"
        return text

    @staticmethod
    async def _display_name(guild: discord.Guild | None, member_id: int) -> str:
        if guild is None:
            return ""
        member = await get_or_fetch_member(guild, member_id)
        return member.display_name if member else ""
