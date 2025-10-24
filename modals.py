import discord

from commands_backend import Commands_Backend
from enum_classes import ChannelType
from submit_collect import Submit_Collect

DISCORD_AVATAR_URL = "https://cdn.discordapp.com/embed/avatars/0.png"

class BasicModal(discord.ui.Modal, title="Edit and Submit Formation"):
    edited_text = discord.ui.TextInput(label="Edit the text", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, bot: discord.Client, backend: Commands_Backend, channel_id: int, original_message: discord.Message):
        super().__init__()
        self.bot = bot
        self.backend = backend
        self.original_message = original_message
        self.channel_id = channel_id
        
        content_msg = original_message.message_snapshots[0] if original_message.flags.forwarded else original_message
        self.edited_text.default = content_msg.content
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        submitter = Submit_Collect(
            bot=self.bot,
            backend=self.backend,
            forwarder=interaction.user,
            channel_id=self.channel_id,
            orig_msg=self.original_message,
            content=self.edited_text.value
            )
        
        formations = await submitter.ctx_submit_message_wrapper()
        await submitter.send_images(interaction, formations)
        await submitter.forward_formation(ChannelType.PRIVATE)
        await submitter.forward_formation(ChannelType.STAFF, formations)
    

class SpreadsheetModal(discord.ui.Modal):
    def __init__(self, bot: discord.Client, backend: Commands_Backend, channel_id: int, show_public: bool=False,
                original_message: discord.Message=None, attachments: list[discord.Attachment]=None):
        super().__init__(title="Submit Formation (by Take)")
            
        self.credits_field = discord.ui.TextInput(
            label="Credits",
            placeholder="(e.g. Frosty)",
            required=False,
            max_length=30
        )
        """
        self.name_field = discord.ui.TextInput(
            label="Data submitter",
            default=author.display_name,
            required=True,
            min_length=1,
            max_length=30
        )
        """
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
            max_length=100
        )
        
        self.bot = bot
        self.backend = backend
        self.channel_id = channel_id
        self.original_message = original_message
        self.attachments = attachments
        self.show_public = show_public
        
        self.add_item(self.credits_field)
        self.add_item(self.damage_field)
        self.add_item(self.resonance_field)
        self.add_item(self.investment_field)
        self.add_item(self.notes_field)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        submitter = Submit_Collect(
            bot=self.bot,
            backend=self.backend,
            forwarder=interaction.user,
            channel_id=self.channel_id,
            orig_msg=self.original_message,
            attachments=self.attachments
            )
        
        submitter.fill_form(
            resonance=self.resonance_field.value,
            ascension=self.investment_field.value,
            credit_name=self.credits_field.value,
            damage=self.damage_field.value,
            notes=self.notes_field.value
            )
        
        formations = await submitter.ctx_submit_message_wrapper()
        msg_or_none: discord.Message = None
        if self.show_public:
            msg_or_none = await submitter.forward_formation(ChannelType.PUBLIC)
            
        url_or_none = msg_or_none.jump_url if msg_or_none else None
            
        await submitter.send_images(interaction, formations)
        
        await submitter.forward_formation(ChannelType.PRIVATE, None, url_or_none)
        msg = await submitter.forward_formation(ChannelType.STAFF, formations, url_or_none)
        
        # Missing check that attachments are actually images
        image_urls = [image.url for image in msg.attachments]
        
        await submitter.send_form(formations, url_or_none, image_urls)