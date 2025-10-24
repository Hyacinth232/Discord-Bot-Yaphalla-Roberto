import io
from asyncio import create_task, gather
from pathlib import Path

import discord

from analyze_image import Analyze_Image
from commands_backend import Commands_Backend
from constants import SERVER_ID, SPAM_CHANNEL_ID
from enum_classes import ChannelType
from google_sheets import add_row
from utils import (to_channel_name, to_channel_type_id, to_priv_id, to_pub_id,
                   to_staff_id)


class Submit_Collect:
    def __init__(self, bot: discord.Client, backend: Commands_Backend, forwarder: discord.Member, channel_id: int, 
                orig_msg: discord.Message=None, attachments: list[discord.Attachment]=None, content: str=None):
        
        self.bot = bot
        self.backend = backend
        self.analyzer = Analyze_Image()
        
        self.forwarder: discord.Member = forwarder
        self.channel_id: int = channel_id
        self.bot_id: int = to_pub_id(channel_id)
        
        self.content = content
        self.form = False
        
        self.attachments: list[discord.Attachment] = attachments
        self.orig_msg: discord.Message = orig_msg
        
        self.has_no_msg = orig_msg is None
        self.url = "No URL" if self.has_no_msg else self.orig_msg.jump_url
        
        self.author_name = ""
        self.forwarder_name = ""
        
        if not self.has_no_msg:
            self.is_forwarded: bool = orig_msg.flags.forwarded
            self.attach_msg: discord.Message = self.orig_msg.message_snapshots[0] if self.is_forwarded else self.orig_msg
            self.attachments = self.attach_msg.attachments
            
        self.attachments = [attachment for attachment in self.attachments 
                            if attachment.content_type and 'image' in attachment.content_type]
        
    def fill_form(self, resonance: str, ascension: str, credit_name: str, damage: str, notes: str):
        self.form = True
        self.resonance = resonance
        self.ascension = ascension
        self.credit_name = credit_name
        self.damage = damage
        self.notes = notes
        
    async def __get_member_name(self, member_id):
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
        author_id = self.forwarder.id if self.has_no_msg else self.orig_msg.author.id
        forwarder_id = self.forwarder.id
        
        self.author_name = await self.__get_member_name(author_id)
        self.forwarder_name = await self.__get_member_name(forwarder_id)
        
        self.counter = await self.backend.users.db.increment_counter(to_channel_name(self.channel_id))
        
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
        files = []
        
        if not formations:
            return files
        
        for i, (units, img_bytes) in enumerate(formations):
            buffer = io.BytesIO(img_bytes)
            buffer.seek(0)
            files.append(discord.File(fp=buffer, filename="formation_{}.png".format(i)))
            
        return files
    
    async def send_images(self, interaction: discord.Interaction, formations: list[tuple], ephemeral: bool=True):
        files = self.formations_to_files(formations)
        if not files:
            await interaction.followup.send("Thank you for the submission!", ephemeral=ephemeral)
            return
        
        await interaction.followup.send(files=files[:10], ephemeral=ephemeral)
        if len(files) >= 10:
            await interaction.followup.send(files=files[10:], ephemeral=ephemeral)
            
    
    async def send_form(self, formations: list[tuple], new_url: str=None, image_urls: list[str]=None):
        if not self.form:
            print("Huh")
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
        
        text += "\n"
        
        if self.form and self.notes:
            text += self.notes
            text += "\n\n"
        
        if self.content:
            text += self.content
            text += "\n\n"
            
        elif not self.has_no_msg and self.attach_msg.content:
            text += self.attach_msg.content
            print(self.attach_msg.content)
            text += "\n\n"
            
        if self.form:
            text += "-# Data exported to tracking sheet! ✅"
        if channel_type == ChannelType.STAFF:
            text += "\n-# Submitted by: {}".format(self.forwarder_name)
        return text
    
    async def get_formation(self, index=-1) -> list[tuple]:
        if not self.attachments:
            return
        
        formations = await self.__process_attachments_driver(index)
        #for image_bytes_stream, units, img_bytes in formations:
        for units, img_bytes in formations:
            # Don't await
            create_task(self.__log_formation(units, img_bytes))
            
        return formations
    
    def make_embeds(self, text: str, footer: str, files: list[discord.File]=None):
        main_embed = discord.Embed(
            url="https://www.yaphalla.com",
            description=text,
            colour=0xa996ff,
            )
        main_embed.set_footer(text=footer)
        embeds = [main_embed]
        
        if not files:
            return embeds
            
        for file in files:
            embed = discord.Embed(url="https://www.yaphalla.com", colour=0xa996ff)
            embed.set_image(url="attachment://{}".format(file.filename))
            embeds.append(embed)
                
        return embeds
    
    """
        Forwards a message to the correct channel
    """
    async def forward_formation(self, channel_type: ChannelType, formations: list[tuple]=None, url: str=None) -> discord.Message:
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
            embeds = self.make_embeds(text, footer, files[:10])
            sent_msg = await channel.send(embeds=embeds, files=files[:10])
        else:
            embeds = self.make_embeds(text, footer)
            sent_msg = await channel.send(embeds=embeds)
            
        return sent_msg
            
    """
        Collects one formation from a given message
    """
    async def __process_attachments_driver(self, index: int=-1) -> list:
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
    
    """
        Calls Analyzer to extract a single formation from one given attachment
    """
    async def __process_attachment(self, attachment: discord.Attachment) -> tuple:
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
        
    """
        Uses Backend to create a formation
    """
    async def __draw_formation(self, units: list) -> str:
        #print(units)
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
        spam_chan = await self.__get_or_fetch_channel(SPAM_CHANNEL_ID)
        if spam_chan:
            await spam_chan.send("Failed to fetch <#{}>".format(channel_id))
    
    """
        Logging everything in the spam channel given by SPAM_CHANNEL_ID
    """
    async def __log_formation(self, units: list, img_bytes):
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
            await spam_chan.send("No characters processed", files=files[:10])
            return
        
        text = self.url
        text += "\n```"
        text += "\n".join(names)
        text += "```"
        await spam_chan.send(text, files=files[:10])
