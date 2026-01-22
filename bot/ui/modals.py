import discord

from bot.core.commands_backend import Commands_Backend
from bot.core.enum_classes import BossType, ChannelType
from bot.submission.submit_collect import Submit_Collect
from bot.ui.embeds import get_embed_image_urls
from bot.ui.views import ReportFormationView

DISCORD_AVATAR_URL = "https://cdn.discordapp.com/embed/avatars/0.png"


class BaseSubmissionModal(discord.ui.Modal):
    """Base modal class for formation submissions with common submission logic."""
    
    def __init__(self, bot: discord.Client, backend: Commands_Backend, channel_id: int,
                original_message: discord.Message = None, attachments: list[discord.Attachment] = None,
                content: str = None, show_public: bool = False, boss_type: BossType = BossType.DREAM_REALM):
        """Initialize base modal with common parameters."""
        super().__init__()
        self.bot = bot
        self.backend = backend
        self.channel_id = channel_id
        self.original_message = original_message
        self.attachments = attachments
        self.content = content
        self.show_public = show_public
        self.boss_type = boss_type
    
    def _create_submitter(self, interaction: discord.Interaction) -> Submit_Collect:
        """Create and return a Submit_Collect instance with common parameters."""
        return Submit_Collect(
            bot=self.bot,
            backend=self.backend,
            forwarder=interaction.user,
            channel_id=self.channel_id,
            orig_msg=self.original_message,
            attachments=self.attachments,
            content=self.content,
            counter_service=self.backend.counter_service,
            boss_type=self.boss_type
        )
    
    async def _handle_common_submission(self, interaction: discord.Interaction, submitter: Submit_Collect) -> tuple[list, str | None, discord.Message | None]:
        """
        Handle common submission flow: get formations, send images, forward to channels.
        
        Returns:
            Tuple of (formations, url_or_none)
        """
        formations = await submitter.ctx_submit_message_wrapper()
        report_view = ReportFormationView()
        msg_or_none: discord.Message = None
        
        if self.show_public:
            msg_or_none = await submitter.forward_formation(ChannelType.PUBLIC)
        
        url_or_none = msg_or_none.jump_url if msg_or_none else None
        
        await submitter.send_images(interaction, formations)
        
        msg =await submitter.forward_formation(ChannelType.PRIVATE, formations, url=url_or_none, report_view=report_view)
        
        image_urls = get_embed_image_urls(msg.embeds)
        formation_urls = [url_dict['proxy_url'] for url_dict in image_urls if url_dict['is_formation']]
        
        return formations, url_or_none, formation_urls


class BasicModal(BaseSubmissionModal, title="Edit and Submit Formation"):
    """Modal for editing and submitting formation text."""
    edited_text = discord.ui.TextInput(label="Edit the text", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, bot: discord.Client, backend: Commands_Backend, channel_id: int, original_message: discord.Message):
        """Initialize modal with bot, backend, and message context."""
        super().__init__(bot, backend, channel_id, original_message=original_message)
        
        content_msg = original_message.message_snapshots[0] if original_message.flags.forwarded else original_message
        self.edited_text.default = content_msg.content
        
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        await interaction.response.defer(ephemeral=True)
        
        self.content = self.edited_text.value
        submitter = self._create_submitter(interaction)
        await self._handle_common_submission(interaction, submitter)
    

class SpreadsheetModal(BaseSubmissionModal, title="Submit Formation (by Take)"):
    """Modal for submitting formation data to spreadsheet."""
    def __init__(self, bot: discord.Client, backend: Commands_Backend, channel_id: int, show_public: bool=False,
                original_message: discord.Message=None, attachments: list[discord.Attachment]=None):
        """Initialize spreadsheet submission modal."""
        super().__init__(bot=bot, backend=backend, channel_id=channel_id, 
                        original_message=original_message, attachments=attachments, show_public=show_public)
            
        self.credits_field = discord.ui.TextInput(
            label="Credits",
            placeholder="(e.g. Frosty)",
            required=False,
            max_length=30
        )
        
        self.damage_field = discord.ui.TextInput(
            label="Damage",
            placeholder="(e.g. 37.1B or 17682M)",
            required=True,
            min_length=2,
            max_length=20
        )
        
        self.resonance_field = discord.ui.TextInput(
            label="Resonance level",
            placeholder="(e.g. 223-225 or 427)",
            required=False,
            min_length=2,
            max_length=10
        )
        
        self.investment_field = discord.ui.TextInput(
            label="DPS Carry's ascension",
            placeholder="(e.g. M+ or P2)",
            required=True,
            min_length=1,
            max_length=10
        )
        
        self.notes_field = discord.ui.TextInput(
            label="Notes",
            style=discord.TextStyle.paragraph,
            required=False,
            min_length=1,
            max_length=1000
        )
        
        self.add_item(self.credits_field)
        self.add_item(self.damage_field)
        self.add_item(self.resonance_field)
        self.add_item(self.investment_field)
        self.add_item(self.notes_field)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle spreadsheet form submission."""
        await interaction.response.defer(ephemeral=True)
        
        submitter = self._create_submitter(interaction)
        
        # Fill form data specific to spreadsheet submission
        submitter.fill_form(
            title="Submission",
            resonance=self.resonance_field.value,
            ascension=self.investment_field.value,
            credit_name=self.credits_field.value,
            damage=self.damage_field.value,
            notes=self.notes_field.value
        )
        
        formations, url_or_none, formation_urls = await self._handle_common_submission(interaction, submitter)
        await submitter.send_form(formations, url_or_none, formation_urls)


class StageSubmissionModal(BaseSubmissionModal, title="Stage Submission"):
    """Modal for submitting stage data with images/videos."""
    def __init__(self, bot: discord.Client, backend: Commands_Backend, channel_id: int, boss_type: BossType,
                attachments: list[discord.Attachment] = None):
        """Initialize stage submission modal."""
        super().__init__(bot=bot, backend=backend, channel_id=channel_id, attachments=attachments, boss_type=boss_type)
        
        self.stage_field = discord.ui.TextInput(
            label="STAGE",
            placeholder="(e.g. S3, P45, SA392, PA979, etc.)",
            required=True,
            min_length=2,
            max_length=8
        )
        
        self.charms_gear_field = discord.ui.TextInput(
            label="Charms/Gear",
            style=discord.TextStyle.paragraph,
            placeholder="Enter charms and gear information...",
            required=False,
            max_length=1000
        )
        
        self.timings_field = discord.ui.TextInput(
            label="Timings",
            style=discord.TextStyle.paragraph,
            placeholder="Enter timing information...",
            required=False,
            max_length=1000
        )
        
        self.replays_field = discord.ui.TextInput(
            label="Replays",
            style=discord.TextStyle.paragraph,
            placeholder="Enter replay links or information...",
            required=False,
            max_length=1000
        )
        
        self.notes_field = discord.ui.TextInput(
            label="Notes",
            style=discord.TextStyle.paragraph,
            placeholder="Enter your notes here...",
            required=False,
            max_length=1000
        )
        
        self.add_item(self.stage_field)
        self.add_item(self.charms_gear_field)
        self.add_item(self.timings_field)
        self.add_item(self.replays_field)
        self.add_item(self.notes_field)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle stage submission form submission."""
        await interaction.response.defer(ephemeral=True)
        
        submitter = self._create_submitter(interaction)
        submitter.fill_stage_form(
            title=self.stage_field.value.upper(),
            charms_gear=self.charms_gear_field.value,
            timings=self.timings_field.value,
            replays=self.replays_field.value,
            notes=self.notes_field.value
        )
        
        await self._handle_common_submission(interaction, submitter)
        
        await interaction.followup.send(
            "Stage submission received! Thank you for your submission.",
            ephemeral=True
        )