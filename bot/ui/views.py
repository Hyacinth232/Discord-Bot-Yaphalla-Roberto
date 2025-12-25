import discord

from bot.core.constants import AMARYLLIS_ID


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


