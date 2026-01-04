import io
from asyncio import create_task, gather
from pathlib import Path

import discord

from bot.core.commands_backend import Commands_Backend
from bot.core.constants import SERVER_ID, SPAM_CHANNEL_ID
from bot.core.enum_classes import ChannelType
from bot.core.utils import (to_channel_name, to_channel_type_id, to_priv_id,
                            to_pub_id, to_staff_id)
from bot.image.analyze_image import Analyze_Image
from bot.services.counter_service import CounterService
from bot.submission.google_sheets import add_row
from bot.ui.embeds import make_embeds
from bot.ui.views import ReportFormationView


class Submit_Collect:
    """Handle formation submission and collection from Discord messages."""
    def __init__(self, bot: discord.Client, backend: Commands_Backend, forwarder: discord.Member, channel_id: int, 
                orig_msg: discord.Message=None, attachments: list[discord.Attachment]=None, content: str=None,
                counter_service: CounterService = None):
        """Initialize submission collector with bot, backend, and message context."""
        self.bot = bot
        self.backend = backend
        self.analyzer = Analyze_Image()
        self.counter_service = counter_service or CounterService(backend.users.db)
        
        self.forwarder: discord.Member = forwarder
        self.channel_id: int = channel_id
        self.bot_id: int = to_pub_id(channel_id)
        
        self.content = content
        self.form = False
        
        self.attachments: list[discord.Attachment] = attachments
        self.orig_msg: discord.Message = orig_msg
        
        self.has_no_msg = orig_msg is None
        self.url = "No URL" if self.has_no_msg else self.orig_msg.jump_url
        self.logged_message_links = []
        
        self.author_name = ""
        self.forwarder_name = ""
        
        if not self.has_no_msg:
            self.is_forwarded: bool = orig_msg.flags.forwarded
            self.attach_msg: discord.Message = self.orig_msg.message_snapshots[0] if self.is_forwarded else self.orig_msg
            self.attachments = self.attach_msg.attachments
            
        self.attachments = [attachment for attachment in self.attachments 
                            if attachment.content_type and 'image' in attachment.content_type]
        
    def fill_form(self, resonance: str, ascension: str, credit_name: str, damage: str, notes: str):
        """Fill form data for spreadsheet submission."""
        self.form = True
        self.resonance = resonance
        self.ascension = ascension
        self.credit_name = credit_name
        self.damage = damage
        self.notes = notes
        
    async def __get_member_name(self, member_id):
        """Get display name for member by ID."""
        try:
            guild = self.bot.get_guild(SERVER_ID)
            if not guild:
                guild = await self.bot.fetch_guild(SERVER_ID)
            
            member = guild.get_member(member_id)
            if not member:
                member = await guild.fetch_member(member_id)
                
            return member.display_name
        except Exception as e:
            print(e)
        return ""
        
    async def ctx_submit_message_wrapper(self) -> list[tuple]:
        """Process message and extract formation data."""
        author_id = self.forwarder.id if self.has_no_msg else self.orig_msg.author.id
        forwarder_id = self.forwarder.id
        
        self.author_name = await self.__get_member_name(author_id)
        self.forwarder_name = await self.__get_member_name(forwarder_id)
        
        self.counter = await self.counter_service.increment(to_channel_name(self.channel_id))
        
        try:
            if not self.has_no_msg:
                create_task(self.orig_msg.add_reaction("📝"))
        except Exception:
            pass
        
        return await self.get_formation()
        
        #tasks = [self.__forward_formation(), self.__forward_formation(bytes_list)]
        #await gather(*tasks)
        
        #create_task(self.__forward_formation())
        #create_task(self.__forward_formation(bytes_list))
        
    def formations_to_files(self, formations: list[tuple]):
        """Convert formation image bytes to Discord file objects."""
        files = []
        
        if not formations:
            return files
        
        for i, (units, img_bytes) in enumerate(formations):
            buffer = io.BytesIO(img_bytes)
            buffer.seek(0)
            files.append(discord.File(fp=buffer, filename="formation_{}.png".format(i)))
            
        return files
    
    async def send_images(self, interaction: discord.Interaction, formations: list[tuple], ephemeral: bool=True):
        """Send formation images to user via Discord interaction."""
        files = self.formations_to_files(formations)
        if not files:
            await interaction.followup.send("Thank you for the submission!", ephemeral=ephemeral)
            return
        
        await interaction.followup.send(files=files[:10], ephemeral=ephemeral)
        if len(files) >= 10:
            await interaction.followup.send(files=files[10:], ephemeral=ephemeral)
            
    
    async def send_form(self, formations: list[tuple], new_url: str=None, image_urls: list[str]=None):
        """Submit form data to Google Sheets."""
        if not self.form:
            return
        
        if self.url != "No URL" or not new_url:
            new_url = self.url
            
        if not formations:
            await add_row(
                self.counter,
                to_channel_name(self.channel_id),
                self.author_name,
                self.resonance,
                self.ascension,
                new_url,
                self.credit_name,
                self.damage,
                self.notes)
            return
        
        total_image_count = len(formations)
        
        for i, (units, img_bytes) in enumerate(formations):
            image_url = image_urls[-(total_image_count - i)] if image_urls else ""
            await add_row(
                self.counter,
                to_channel_name(self.channel_id),
                self.author_name,
                self.resonance,
                self.ascension,
                new_url,
                self.credit_name,
                self.damage,
                self.notes,
                units,
                image_url)
        
    async def __get_text(self, channel_type: ChannelType, new_url: str=None) -> str:
        """Generate formatted text for submission message."""
        text = "## Submission\n"
        if channel_type == ChannelType.STAFF:
            text += "**ID:** {}\n".format(self.counter)
        
        if self.url != "No URL":
            text += "**Link:** {}\n".format(self.url)
        elif new_url:
            text += "**Link:** {}\n".format(new_url)
            
        text += "**From:** {}\n".format(self.author_name)
        #text += "Forwarder: {}, ".format(self.forwarder.mention)
        #if self.is_forwarded: text += "**FORWARDED**\n"
        
        if self.form:
            text += "**Credits:** {}\n".format(self.credit_name)
            text += "**Damage:** {}\n".format(self.damage)
            text += "**Ascension:** {}\n".format(self.ascension)
            text += "**Resonance** {}\n".format(self.resonance)
        
        text += "\n"
        
        if self.form and self.notes:
            text += self.notes
            text += "\n\n"
        
        if self.content:
            text += self.content
            text += "\n\n"
            
        elif not self.has_no_msg and self.attach_msg.content:
            text += self.attach_msg.content
            # print(self.attach_msg.content)
            text += "\n\n"
            
        if self.form:
            text += "-# Data exported to tracking sheet! ✅"
        if channel_type == ChannelType.STAFF:
            text += "\n-# Submitted by: {}".format(self.forwarder_name)
        return text
    
    async def get_formation(self, index=-1) -> list[tuple]:
        """Extract formation data from attachments."""
        if not self.attachments:
            return
        
        formations = await self.__process_attachments_driver(index)
        self.logged_message_links = []
        for units, img_bytes in formations:
            logged_msg = await self.__log_formation(units, img_bytes)
            if logged_msg:
                self.logged_message_links.append(logged_msg.jump_url)
            
        return formations
    
    
    async def forward_formation(self, channel_type: ChannelType, formations: list[tuple]=None, url: str=None, report_view: ReportFormationView=None) -> discord.Message:
        """Forward formation submission to appropriate channel."""
        files = []
        
        # If there are any images to forward
        if self.attachments:
            for i, attachment in enumerate(self.attachments):
                ext = Path(attachment.filename).suffix
                new_filename = "img_{}{}".format(i, ext)
                file = await attachment.to_file(filename=new_filename)
                files.append(file)
            #files = [await attachment.to_file() for attachment in self.attachments]
            
        # If there are any yapbuilder formations to forward
        if formations:
            formation_files = self.formations_to_files(formations)
            files.extend(formation_files)
            
        # Retrieve channel based on channel type
        channel = await self.__get_or_fetch_channel(to_channel_type_id(channel_type, self.channel_id))
        sent_msg: discord.Message = None
        
        text = await self.__get_text(channel_type, url)
        
        if channel_type == ChannelType.STAFF:
            if files:
                sent_msg = await channel.send("Filler", files=files[:10])
                if len(files) > 10:
                    await channel.send(files=files[10:])
            else:
                sent_msg = await channel.send("Filler")
            await sent_msg.edit(content=text)
            
            return sent_msg
        
        
        footer = "ID: {} | Submitted by: {}".format(self.counter, self.forwarder_name)
        if files:
            embeds = make_embeds(text, footer, files[:10], self.logged_message_links)
            sent_msg = await channel.send(embeds=embeds, files=files[:10], view=report_view)
        else:
            embeds = make_embeds(text, footer, None, self.logged_message_links)
            sent_msg = await channel.send(embeds=embeds)
            
        return sent_msg
            
    async def __process_attachments_driver(self, index: int=-1) -> list:
        """Process all attachments or specific index to extract formations."""
        if index != -1:
            index = min(max(index - 1, 0), len(self.attachments) - 1)
            formation = await self.__process_attachment(self.attachments[index])
            return [formation] if formation else []
        
        #tasks = [self.__process_attachment(attachment) for attachment in self.attachments]
        #formations = await gather(*tasks)
        
        formations = []
        for attachment in self.attachments:
            formation = await self.__process_attachment(attachment)
            if formation:
                formations.append(formation)
            
        return formations
    
    async def __process_attachment(self, attachment: discord.Attachment) -> tuple:
        """Extract formation data from single attachment using image analyzer."""
        if not attachment.content_type or 'image' not in attachment.content_type:
            return None
        
        image_bytes = await attachment.read()
        units = self.analyzer.process_image(image_bytes)
        units = [unit for unit in units if unit is not None]
        
        if not units or len(units) < 3:
            return None
        
        yapbuilder_filename = await self.__draw_formation(units)
        
        image_bytes = None
        with open(yapbuilder_filename, "rb") as f:
            img_bytes = f.read()
            
        return (units, img_bytes)
        
    async def __draw_formation(self, units: list) -> str:
        """Generate formation image using backend."""
        pairs = ["{} {}".format(unit['name'], unit['number']) for unit in units]
        chan_name = to_channel_name(self.channel_id)
        if chan_name is not None and "Nocturne Judicator" in chan_name:
            pairs.append("Hunter 13")
        pairs = ' '.join(pairs)
            
        self.backend.set_settings(user_id=self.bot_id, key='show_numbers', value=False)
        self.backend.clear_user(user_id=self.bot_id)
        self.backend.add_list(user_id=self.bot_id, pairs=pairs)

        filename = self.backend.show_image(user_id=self.bot_id, is_private=False)
        return filename
    
    async def __get_or_fetch_channel(self, channel_id: int) -> discord.abc.GuildChannel | discord.Thread | None:
        """Get or fetch Discord channel by ID."""
        channel: discord.channel = None
        try:
            guild = self.bot.get_guild(SERVER_ID)
            if not guild:
                guild = await self.bot.fetch_guild(SERVER_ID)
            
            channel = guild.get_channel(channel_id)
            if not channel:
                channel = await guild.fetch_channel(channel_id)
            
        except Exception as e:
            print(e)
            
        return channel
    
    async def __channel_fetch_fail(self, channel_id: int):
        """Log channel fetch failure to spam channel."""
        spam_chan = await self.__get_or_fetch_channel(SPAM_CHANNEL_ID)
        if spam_chan:
            await spam_chan.send("Failed to fetch <#{}>".format(channel_id))
    
    async def __log_formation(self, units: list, img_bytes) -> discord.Message:
        """Log formation data to spam channel for debugging. Returns the sent message."""
        spam_chan = await self.__get_or_fetch_channel(SPAM_CHANNEL_ID)
        files = []
        if img_bytes:
            buffer = io.BytesIO(img_bytes)
            buffer.seek(0)
            files.append(discord.File(fp=buffer, filename="formation.png"))
        #if image_bytes_stream:
        #    files.append(discord.File(fp=image_bytes_stream, filename="src_image.png"))
        
        names = []
        for dictionary in units:
            filename = "{}_{}.png".format(dictionary['name'], dictionary['number'])
            names.append(filename)
            if dictionary['image']:
                files.append(discord.File(fp=dictionary['image'], filename=filename))

        if not names:
            return await spam_chan.send("No characters processed", files=files[:10])
        
        text = self.url
        text += "\n```\n"
        text += "\n".join(names)
        text += "\n```"
        return await spam_chan.send(text, files=files[:10])
