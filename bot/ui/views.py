import io

import aiohttp
import discord

from bot.core.constants import (AMARYLLIS_ID, SERVER_ID, SPAM_CHANNEL_ID,
                                WAITER_ROLE_IDS)
from bot.core.utils import to_channel_name
from bot.submission.google_sheets import clear_image_str
from bot.ui.embeds import make_embeds


class YesNoView(discord.ui.View):
    """View with Yes/No buttons for user confirmation."""
    def __init__(self, user_id):
        """Initialize view with user ID for permission checking."""
        super().__init__()
        self.user_id = user_id
        self.result = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Yes button click."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You can't use this button.", ephemeral=True)
        
        self.result = True
        await interaction.response.edit_message(content="Proceeding...", view=None)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle No button click."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You cannot use this button.", ephemeral=True)
        
        self.result = False
        await interaction.response.edit_message(content="Your action has been canceled.", view=None)
        self.stop()
        
class Dropdown(discord.ui.Select):
    """Dropdown select menu for boss selection."""
    def __init__(self, options: list, placeholder: str, callback_func):
        """Initialize dropdown with options and callback."""
        self.callback_func = callback_func
        options = [discord.SelectOption(label=key) for key in options]
        super().__init__(placeholder=placeholder, options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection."""
        ephemeral = False if interaction.user.id == AMARYLLIS_ID else True
        await self.callback_func(interaction, self.values[0], ephemeral)

class DropdownView(discord.ui.View):
    """View containing a dropdown select menu."""
    def __init__(self, options: list, placeholder: str, callback_func):
        """Initialize view with dropdown."""
        super().__init__(timeout=300)
        self.dropdown = Dropdown(options, placeholder, callback_func)
        self.add_item(self.dropdown)
        self.message = None
        
    async def on_timeout(self):
        """Disable dropdown when view times out."""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass


class ReportConfirmationView(discord.ui.View):
    """View for confirming formation misidentification report."""
    def __init__(self, message: discord.Message):
        """Initialize confirmation view with message context."""
        super().__init__(timeout=60)
        self.message = message
        self.confirmed = False
    
    """async def interaction_check(self, interaction: discord.Interaction) -> bool:
        "Check if user has permission to interact with this view."
        if interaction.guild is None or interaction.guild.id != SERVER_ID:
            return False
        if interaction.user.id == AMARYLLIS_ID:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        return any(role.id in WAITER_ROLE_IDS for role in interaction.user.roles)
        """
    
    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Continue button click."""
        self.confirmed = True
        await interaction.response.defer(ephemeral=True)
        
        try:
            await interaction.edit_original_response(
                content="Thank you for reporting! The formation has been flagged for review.",
                view=None
            )
        except Exception:
            pass
        
        await _process_report(interaction, self.message)
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Cancel button click."""
        await interaction.response.edit_message(
            content="Report cancelled.",
            view=None
        )
        self.stop()
    
    async def on_timeout(self):
        """Disable buttons when view times out."""
        for item in self.children:
            item.disabled = True


class ReportFormationView(discord.ui.View):
    """Persistent view with button to report incorrect formation identification."""
    def __init__(self):
        """Initialize persistent view with no timeout."""
        super().__init__(timeout=None)
    
    """
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        "Check if user has permission to interact with this view."
        if interaction.guild is None or interaction.guild.id != SERVER_ID:
            return False
        if interaction.user.id == AMARYLLIS_ID:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        return any(role.id in WAITER_ROLE_IDS for role in interaction.user.roles)
    """
    
    @discord.ui.button(
        label='Report Image Misidentification',
        style=discord.ButtonStyle.red,
        custom_id='roberto:report_formation'
    )
    async def report_formation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle report button click - shows confirmation view."""
        message = interaction.message
        if not message:
            await interaction.response.send_message("Unable to find the submission message.", ephemeral=True)
            return
        
        confirmation_view = ReportConfirmationView(message)
        await interaction.response.send_message(
            "This sends the image to the graphics team for review. Continue?",
            view=confirmation_view,
            ephemeral=True
        )


async def _process_report(interaction: discord.Interaction, message: discord.Message):
    """Process the actual report after confirmation."""
    bot = interaction.client
    
    try:
        guild = bot.get_guild(SERVER_ID)
        if not guild:
            guild = await bot.fetch_guild(SERVER_ID)
        
        spam_channel = guild.get_channel(SPAM_CHANNEL_ID)
        if not spam_channel:
            spam_channel = await guild.fetch_channel(SPAM_CHANNEL_ID)
        
        report_text = "**Formation Misidentification Report**\n"
        report_text += f"**Reported by:** {interaction.user.mention}\n"
        report_text += f"**Submission Message:** {message.jump_url}\n"
        
        submission_id = None
        if message.embeds:
            for embed in message.embeds:
                if embed.footer and embed.footer.text:
                    if "ID:" in embed.footer.text:
                        submission_id = embed.footer.text.split('ID:')[1].split('|')[0].strip()
                        report_text += f"**Submission ID:** {submission_id}\n"
        
        report_text += f"<@{AMARYLLIS_ID}>"
        msg = await spam_channel.send(f"<@{AMARYLLIS_ID}>")
        await msg.edit(content=report_text)
        
        if submission_id:
            try:
                boss_name = to_channel_name(message.channel.id)
                if boss_name:
                    await clear_image_str(int(submission_id), boss_name)
            except Exception as e:
                print(f"Error clearing image_str from spreadsheet: {e}")
        
        text = message.embeds[0].description
        footer = message.embeds[0].footer.text
        
        filtered_files = []
        for embed in message.embeds:
            if embed.image and embed.image.url:
                if 'formation_' not in embed.image.url:
                    if embed.image.proxy_url:
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(embed.image.proxy_url) as resp:
                                    if resp.status == 200:
                                        image_data = await resp.read()
                                        if embed.image.url.startswith('attachment://'):
                                            filename = embed.image.url.replace('attachment://', '')
                                        else:
                                            filename = embed.image.proxy_url.split('/')[-1].split('?')[0] or f"image_{len(filtered_files)}.png"
                                        filtered_files.append(discord.File(io.BytesIO(image_data), filename=filename))
                        except Exception as e:
                            print(f"Failed to download image from embed: {e}")
        
        try:
            channel = message.channel
            embeds = make_embeds(text, footer, filtered_files)
            try:
                await message.edit(embeds=embeds, attachments=filtered_files, view=None)
            except discord.errors.HTTPException:
                # If editing fails, delete and resend
                try:
                    await message.delete()
                    await channel.send(embeds=embeds, files=filtered_files, view=None)
                except Exception as e:
                    print(f"Failed to delete and resend message: {e}")
        except Exception as e:
            print(f"Error processing message edit: {e}")
        
    except Exception as e:
        submission_id = None
        try:
            if message.embeds:
                for embed in message.embeds:
                    if embed.footer and embed.footer.text:
                        if "ID:" in embed.footer.text:
                            submission_id = embed.footer.text.split('ID:')[1].split('|')[0].strip()
        except:
            pass
        
        ping_text = ""
        if submission_id:
            ping_text += f"submission #{submission_id} "
        ping_text += f"<@{AMARYLLIS_ID}>"
            
        await interaction.followup.send(
            "An error occurred while reporting " + ping_text,
            ephemeral=False
        )

