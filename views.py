import discord

from constants import AMARYLLIS_ID


class YesNoView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.result = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You can't use this button.", ephemeral=True)
        
        self.result = True
        await interaction.response.edit_message(content="Proceeding...", view=None)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You cannot use this button.", ephemeral=True)
        
        self.result = False
        await interaction.response.edit_message(content="Your action has been canceled.", view=None)
        self.stop()
        
class Dropdown(discord.ui.Select):
    def __init__(self, options: list, placeholder: str, callback_func):
        self.callback_func = callback_func
        options = [discord.SelectOption(label=key) for key in options]
        super().__init__(placeholder=placeholder, options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        """if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this dropdown.", ephemeral=True)
            return
        """
        ephemeral = False if interaction.user.id == AMARYLLIS_ID else True
        await self.callback_func(interaction, self.values[0], ephemeral)
        
        #await interaction.response.defer()
        #self.view.stop()

class DropdownView(discord.ui.View):
    def __init__(self, options: list, placeholder: str, callback_func):
        super().__init__(timeout=300)
        self.dropdown = Dropdown(options, placeholder, callback_func)
        self.add_item(self.dropdown)
        self.message = None
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass


