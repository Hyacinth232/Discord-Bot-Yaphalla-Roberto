import io
from datetime import datetime, timezone

import discord
from discord.ext import commands

from commands_backend import Commands_Backend
from constants import (AMARYLLIS_ID, CHANNEL_IDS_DICT, PRIVATE_CHANNEL_IDS,
                       PUBLIC_CHANNEL_IDS, ROBERTO_TEXT, SERVER_ID, setup_json)
from enum_classes import TRANSLATE, ChannelType, Language
from modals import BasicModal, SpreadsheetModal
from submit_collect import Submit_Collect
from utils import (clean_input_str, get_emoji, is_kitchen_channel,
                   replace_emojis)
from views import DropdownView, YesNoView

#s4 START_DATE = datetime(2025, 5, 23, tzinfo=timezone.utc)
# s5
START_DATE = datetime(2025, 9, 26, tzinfo=timezone.utc)

def clean_name(text: str):
    return clean_input_str(text)[:35]

def get_emojis(names: list[str]) -> str:
    return " ".join([get_emoji(name) for name in names])

class Commands_Frontend:
    def __init__(self, bot: discord.Client):
        self.backend = Commands_Backend()
        self.bot = bot

    def infographic(self, value: dict) -> str:
        text = value.get('text', '')
        timestamp = value.get('timestamp', '')
        
        result = "{}\n".format(text)
        result += "<t:{}>".format(timestamp)
        return result
    
    async def get_image_embed(self, interaction: discord.Interaction, key: str, ephemeral=False):
        value = self.backend.users.db.get_image_link(key)
        infographic = self.infographic(value)
        await interaction.response.send_message(infographic, ephemeral=ephemeral)
    
    def get_names_list(self, user_id: int):
        return self.backend.get_names_list(user_id)
    """
        Error message
    """
    async def error_message(self, interaction: discord.Interaction, lang: Language=Language.EN, followup=False):
        if followup:
            await interaction.followup.send(TRANSLATE['Error'][lang], ephemeral=True)
        else:
            await interaction.response.send_message(TRANSLATE['Error'][lang], ephemeral=True)
            
    """
        Add text to mongodb databse
    """
    async def set_image_link(self, interaction: discord.Interaction, key: str, text: str):
        timestamp = int(datetime.now(timezone.utc).timestamp())
        text = replace_emojis(text)
        self.backend.users.db.set_image_link(key, text, timestamp)
        
        value = self.backend.users.db.get_image_link(key)
        infographic = self.infographic(value)
        await interaction.response.send_message(infographic)
    
    """
        Emojies
    """
    async def emojify_wrapper(self, interaction: discord.Interaction, text: str):
        text = replace_emojis(text)
        await interaction.response.send_message(text, ephemeral=False)
        
    async def emoji_wrapper(self, interaction: discord.Interaction, name: str, show_public: bool):
        emoji = self.backend.name_to_emoji(name)
        if emoji:
            await interaction.response.send_message(emoji, ephemeral=not show_public)
            return
        await interaction.response.send_message("Invalid name.", ephemeral=not show_public)
        
    """
        Edit formation
    """
    async def add_wrapper(self, interaction: discord.Interaction, pairs: str, lang: Language=Language.EN):
        added_names, filename = self.backend.add_list(interaction.user.id, pairs)
        
        if added_names:
            await interaction.response.send_message("{}{}".format(TRANSLATE["Added"][lang], get_emojis(added_names)), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
        
    async def remove_wrapper(self, interaction: discord.Interaction, names_or_indices: str, lang: Language=Language.EN):
        removed_names, filename = self.backend.remove_list(interaction.user.id, names_or_indices)
        
        if removed_names:
            await interaction.response.send_message("{}{}".format(TRANSLATE["Removed"][lang], get_emojis(removed_names)), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
        
    async def swap_wrapper(self, interaction: discord.Interaction, pairs: str, lang: Language=Language.EN):
        swapped_names, filename = self.backend.swap_list(interaction.user.id, pairs)
        if swapped_names:
            await interaction.response.send_message("{}{}".format(TRANSLATE['Swapped'][lang], get_emojis(swapped_names)), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
            
    async def add_one_wrapper(self, interaction: discord.Interaction, unit: str, idx: int, lang: Language=Language.EN):
        name, filename = self.backend.add_one(interaction.user.id, unit, idx)
        
        if name:
            await interaction.response.send_message("{}{}".format(TRANSLATE["Added"][lang], get_emoji(name)), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
            
    async def remove_one_wrapper(self, interaction: discord.Interaction, name: str, lang: Language=Language.EN):
        name, filename = self.backend.remove_one(interaction.user.id, name)
        
        if name:
            await interaction.response.send_message("{}{}".format(TRANSLATE["Removed"][lang], get_emoji(name)), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
        
    async def swap_pair_wrapper(self, interaction: discord.Interaction, name1: str, name2: str, lang: Language=Language.EN):
        swapped_names, filename = self.backend.swap_pair(interaction.user.id, name1, name2)
        if swapped_names:
            await interaction.response.send_message("{}{}".format(TRANSLATE['Swapped'][lang], get_emojis(swapped_names)), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
            
    async def move_one_wrapper(self, interaction: discord.Interaction, name: str, idx: int, lang: Language=Language.EN):
        name, filename = self.backend.move_one(interaction.user.id, name, idx)
        if name:
            await interaction.response.send_message("{}{}".format('Moved ', get_emoji(name)), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
                
    async def display_formation_wrapper(self, interaction: discord.Interaction, ephemeral=True, display_mode=False):
        user_id = interaction.user.id
        self.backend.initialize_user(user_id)
        filename = self.backend.show_image(user_id=user_id, is_private=not display_mode)
        await interaction.response.send_message(file=discord.File(filename), ephemeral=ephemeral)
        
    async def clear_wrapper(self, interaction: discord.Interaction, lang: Language=Language.EN):
        filename = self.backend.clear_user(interaction.user.id)
        await interaction.response.send_message(TRANSLATE['Clear'][lang], ephemeral=True)
        await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        
    async def mirror_wrapper(self, interaction: discord.Interaction, lang: Language=Language.EN):
        filename = self.backend.mirror_formation(interaction.user.id)
        await interaction.response.send_message('Mirrored formation', ephemeral=True)
        await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        
    async def set_map_wrapper(self, interaction: discord.Interaction, map: str, user_id: int=None, save_map: bool=False, lang: Language=Language.EN):
        if user_id is None:
            user_id = interaction.user.id
        #map = clean_name(map)
        map, filename = self.backend.set_map(user_id, map)
        if save_map:
            success, new_name = self.backend.update_formation(user_id)
        if map:
            await interaction.response.send_message('Set map to {}'.format(map), ephemeral=not save_map)
            await interaction.followup.send(file=discord.File(filename), ephemeral=not save_map)
        else:
            await self.error_message(interaction, lang)
            
    async def set_name_wrapper(self, interaction: discord.Interaction, title: str, lang: Language=Language.EN):
        user_id = interaction.user.id
        title = clean_name(title)
        title = self.backend.set_name(user_id, title)
        if title:
            await interaction.response.send_message('Set title. Make sure to use `/show_title`.', ephemeral=True)
        else:
            await self.error_message(interaction, lang)
            
    async def show_title_wrapper(self, interaction: discord.Interaction, show_title: bool, lang: Language=Language.EN):
        filename = self.backend.set_settings(interaction.user.id, 'show_title', show_title)
        if show_title:
            await interaction.response.send_message('Showing title.', ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
            return
        
        if not show_title:
            await interaction.response.send_message('Hiding title.', ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
            
    async def show_numbers_wrapper(self, interaction: discord.Interaction, show_numbers: bool, lang: Language=Language.EN):
        filename = self.backend.set_settings(interaction.user.id, 'show_numbers', show_numbers)
        if show_numbers:
            await interaction.response.send_message('Showing tile numbers.', ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
            return
        
        if not show_numbers:
            await interaction.response.send_message('Hiding tile numbers.', ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
            
    async def make_transparent_wrapper(self, interaction: discord.Interaction, make_transparent: bool, lang: Language=Language.EN):
        filename = self.backend.set_settings(interaction.user.id, 'make_transparent', make_transparent)
        if make_transparent:
            await interaction.response.send_message('Base tiles are now transparent.', ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
            return
        
        if not make_transparent:
            await interaction.response.send_message('Base tiles are now opaque.', ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
            
    async def set_base_hex(self, interaction: discord.Interaction, idx: int, hex_name: str,
                           user_id = None, lang: Language=Language.EN, ephemeral=True):
        if user_id is None:
            user_id = interaction.user.id
            
        filename = self.backend.set_base_hex(user_id, idx, hex_name)
        if not filename:
            await self.error_message(interaction, lang)
            return
            
        filename = self.backend.show_image(user_id=user_id, is_private=False)
        if filename:
            await interaction.response.send_message('Base hex has been changed.', ephemeral=ephemeral)
            await interaction.followup.send(file=discord.File(filename), ephemeral=ephemeral)
        else:
            await self.error_message(interaction, lang)
            
    async def yap_set_base_hex(self, interaction: discord.Interaction, fill_name: str, line_name: str, make_transparent: bool,
                           user_id = None, lang: Language=Language.EN, ephemeral=False):
        if user_id is None:
            user_id = interaction.user.id
            
        filename = self.backend.set_settings(user_id, 'make_transparent', make_transparent)
        if not make_transparent:
            filename = self.backend.set_base_hex(user_id, 0, fill_name)
            
        filename = self.backend.set_base_hex(user_id, 1, line_name)
        
        if not filename:
            await self.error_message(interaction, lang)
            return
            
        filename = self.backend.show_image(user_id=user_id, is_private=False)
        if filename:
            #await interaction.response.send_message('Base hex has been changed.', ephemeral=ephemeral)
            await interaction.response.send_message(file=discord.File(filename), ephemeral=ephemeral)
        else:
            await self.error_message(interaction, lang)
            
    async def load_wrapper(self, interaction: discord.Interaction, name: str, lang: Language=Language.EN):
        user_id = interaction.user.id
        name = clean_name(name)
        
        await interaction.response.defer(ephemeral=True)
        
        names_lst = self.backend.get_names_list(user_id)
        if name not in names_lst:
            await interaction.followup.send("The formation you are trying to load does not exist.", ephemeral=True)
            return
        
        save_status = self.backend.get_save_status(user_id)
        if not save_status:
            view = YesNoView(user_id)
            await interaction.followup.send(
                "Your current formation has not been saved. Are you sure you wish to proceed?",
                view=view, ephemeral=True)
            
            await view.wait()
            if not view.result: return
        
        success, filename, name = self.backend.load_formation(user_id, name)
        
        if success:
            await interaction.followup.send("Loading new formation: {}".format(name), ephemeral=True)
            await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        else:
            await self.error_message(interaction, lang, True)
            
    async def delete_wrapper(self, interaction: discord.Interaction, name: str, lang: Language=Language.EN):
        user_id = interaction.user.id
        name = clean_name(name)
        names_lst = self.backend.get_names_list(user_id)
        
        if name not in names_lst:
            await interaction.response.send_message("The formation you are trying to delete does not exist.", ephemeral=True)
            return
        
        curr_name = self.backend.get_name(user_id)
        if curr_name == name:
            await interaction.response.send_message("The current formation cannot be deleted.", ephemeral=True)
            return
            
        success, name = self.backend.delete_formation(user_id, name)
        if success:
            await interaction.response.send_message("Formation `{}` has been deleted.".format(name), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
            
    async def list_formations_wrapper(self, interaction: discord.Interaction, lang: Language=Language.EN):
        user_id = interaction.user.id
        await interaction.response.send_message("```{}```".format(', '.join(self.get_names_list(user_id))), ephemeral=True)
        
    async def current_name_wrapper(self, interaction: discord.Interaction, lang: Language=Language.EN):
        user_id = interaction.user.id
        name = self.backend.get_name(user_id)
        await interaction.response.send_message("Your current formation name is `{}`.".format(name), ephemeral=True)
        
    async def save_wrapper(self, interaction: discord.Interaction, lang: Language=Language.EN):
        user_id = interaction.user.id
        success, new_name = self.backend.update_formation(user_id)
        if success:
            await interaction.response.send_message("Formation has been saved as `{}`.".format(new_name), ephemeral=True)
        else:
            await self.error_message(interaction, lang)
            
    async def rename_wrapper(self, interaction: discord.Interaction, new_name: str, lang: Language=Language.EN):
        user_id = interaction.user.id
        new_name = clean_name(new_name)
        names_lst = self.backend.get_names_list(user_id)
        await interaction.response.defer(ephemeral=True)

        if new_name in names_lst:
            view = YesNoView(user_id)
            await interaction.followup.send(
                "The name `{}` already exists. Do you wish to proceed and overwrite your existing formation?".format(new_name),
                view=view, ephemeral=True)
            
            await view.wait()
            if not view.result: return
            
        old_name = self.backend.get_name(user_id)
        success, new_name = self.backend.rename_other_formation(user_id, old_name, new_name)
        
        if success:
            await interaction.followup.send("Formation has been renamed to `{}`.".format(new_name), ephemeral=True)
        else:
            await self.error_message(interaction, lang, True)
            
    async def save_as_wrapper(self, interaction: discord.Interaction, new_name: str, lang: Language=Language.EN):
        user_id = interaction.user.id
        new_name = clean_name(new_name)
        names_lst = self.backend.get_names_list(user_id)
        await interaction.response.defer(ephemeral=True)
        
        if len(names_lst) >= 20:
            await interaction.followup.send("You can only have up to 20 formations.", ephemeral=True)
            return
        
        if new_name in names_lst:
            view = YesNoView(user_id)
            await interaction.followup.send(
                "The name `{}` already exists. Do you wish to proceed and overwrite your existing formation?".format(new_name),
                view=view, ephemeral=True)
            
            await view.wait()
            if not view.result: return
            
            success, new_name = self.backend.overwrite_formation(user_id, new_name)
        else:
            success, new_name = self.backend.add_formation(user_id, new_name)
            
        if success:
            await interaction.followup.send("Formation has been saved as `{}`.".format(new_name), ephemeral=True)
        else:
            await self.error_message(interaction, lang, True)
            
    async def dropdown_wrapper(self, interaction: discord.Interaction, game_mode: str):
        text = '\n'.join(["<#{}>".format(PUBLIC_CHANNEL_IDS[boss_name]) for boss_name in setup_json[game_mode]])
        text += '\n\nView Boss Infographs by selecting a Boss below.'
        title = game_mode.replace('_', ' ').title()
                
        embed = discord.Embed(
            title='S5 {}'.format(title),
            description=text,
            color=discord.Color.fuchsia(),
        )
        
        view = DropdownView(setup_json[game_mode], 'Select a Boss...', self.get_image_embed)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        view.message = await interaction.original_response()
    
    async def get_timestamp(self, interaction: discord.Interaction, year: int, month: int, day: int, hour: int):
        try:
            dt = datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)
            unix_timestamp = int(dt.timestamp())
            await interaction.response.send_message("<t:{}:F>".format(unix_timestamp))
        except ValueError:
            await self.error_message(interaction)
    
    async def time_now_wrapper(self, interaction: discord.Interaction):
        try:
            dt = datetime.now(timezone.utc)
            unix_timestamp = int(dt.timestamp())
            await interaction.response.send_message("<t:{}:f>".format(unix_timestamp))
        except ValueError:
            await self.error_message(interaction)
            
    async def collect_wrapper(self, ctx: commands.Context, index: int):
        if not ctx.message.reference:
            return
        
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        
        submitter = Submit_Collect(
            bot=self.bot,
            backend=self.backend,
            forwarder=ctx.author,
            channel_id=ctx.channel.id,
            orig_msg=replied_message)
        
        formations = await submitter.get_formation(index)
        files = submitter.formations_to_files(formations)
        if not files:
            return
        
        await ctx.channel.send(files=files[:10])
        if len(files) >= 10:
            await ctx.channel.send(files=files[10:])
            
    async def context_no_modal_wrapper(self, interaction: discord.Interaction, message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            await interaction.response.send_message("Submissions are only allowed from Yaphalla", ephemeral=True)
            return
        
        channel_id = message.channel.id
        if not is_kitchen_channel(channel_id):
            await interaction.response.send_message("Submissions are only allowed from Kitchen channels", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        submitter = Submit_Collect(
            bot=self.bot,
            backend=self.backend,
            forwarder=interaction.user,
            channel_id=channel_id,
            orig_msg=message
            )
        
        formations = await submitter.ctx_submit_message_wrapper()
        await submitter.send_images(interaction, formations)
        await submitter.forward_formation(ChannelType.PRIVATE)
        await submitter.forward_formation(ChannelType.STAFF, formations)

    async def context_basic_modal_wrapper(self, interaction: discord.Interaction, message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            await interaction.response.send_message("Submissions are only allowed from Yaphalla", ephemeral=True)
            return
        
        channel_id = message.channel.id
        if not is_kitchen_channel(channel_id):
            await interaction.response.send_message("Submissions are only allowed from Kitchen channels", ephemeral=True)
            return
        
        modal = BasicModal(self.bot, self.backend, channel_id, message)
        await interaction.response.send_modal(modal)
        
    async def context_form_modal_wrapper(self, interaction: discord.Interaction, message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            await interaction.response.send_message("Submissions are only allowed from Yaphalla", ephemeral=True)
            return
        
        channel_id = message.channel.id
        if not is_kitchen_channel(channel_id):
            await interaction.response.send_message("Submissions are only allowed from Kitchen channels", ephemeral=True)
            return
        
        modal = SpreadsheetModal(
            bot=self.bot,
            backend=self.backend,
            channel_id=channel_id,
            show_public=False,
            original_message=message
            )
        await interaction.response.send_modal(modal)
        
    async def command_form_modal_wrapper(self, interaction: discord.Interaction, attachments: list[discord.Attachment]):
        attachments = [attachment for attachment in attachments if attachment is not None]
        
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("Submissions are only allowed from Yaphalla", ephemeral=True)
            return
        
        channel_id = interaction.channel.id
        if not is_kitchen_channel(channel_id):
            await interaction.response.send_message("Submissions are only allowed from Kitchen channels", ephemeral=True)
            return
        
        modal = SpreadsheetModal(
            bot=self.bot,
            backend=self.backend,
            channel_id=channel_id,
            show_public=True,
            original_message=None,
            attachments=attachments
            )
        
        await interaction.response.send_modal(modal)
            
    async def submit_wrapper(self, ctx: commands.Context):
        if not ctx.guild or ctx.guild.id != SERVER_ID: return
        
        if not ctx.message.reference:
            """my_files = [
                discord.File("Sample_Formation.png"),
                discord.File("Sample_Team.png"),
                discord.File("Sample_Damage.png")
            ]
            #await ctx.send("Please reply to the message you want to submit with `!submit`.")
            
            await ctx.send(content=ROBERTO_TEXT, files=my_files)
            """
            return
        
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        channel_id = replied_message.channel.id
        if not is_kitchen_channel(channel_id):
            return
        
        submitter = Submit_Collect(
            bot=self.bot,
            backend=self.backend,
            forwarder=ctx.author,
            channel_id=channel_id,
            orig_msg=replied_message
            )
        
        formations = await submitter.ctx_submit_message_wrapper()
        await submitter.forward_formation(ChannelType.PRIVATE)
        await submitter.forward_formation(ChannelType.STAFF, formations)
        
    async def add_permissions(self, bot: discord.Client):
        
        guild = bot.get_guild(SERVER_ID)
        for game_mode in ['dream_realm', 'primal_lords']:
            for boss_name in setup_json[game_mode]:
                try:
                    private_channel = guild.get_channel(PRIVATE_CHANNEL_IDS[boss_name])
                    overwrite = discord.PermissionOverwrite()
                    waiter = guild.get_role(1366553846234746971)
                    editor = guild.get_role(1366553665816625253)
                    overwrite.send_messages=True
                        
                    await private_channel.set_permissions(waiter, overwrite=overwrite)
                    await private_channel.set_permissions(editor, overwrite=overwrite)
                    
                except Exception as e:
                    pass
        
    async def rotate_channels(self, bot: discord.Client):
        game_mode = 'dream_realm'
        
        owner = await bot.fetch_user(AMARYLLIS_ID)
        guild = bot.get_guild(SERVER_ID)
        if guild is None:
            print("Server not found.")
            return

        elapsed_days = (datetime.now(timezone.utc) - START_DATE).days
        
        count = len(setup_json[game_mode])
        today_boss = setup_json[game_mode][elapsed_days % count]
        tomorrow_boss = setup_json[game_mode][(elapsed_days + 1) % count]
        
        """for boss_name in setup_json[game_mode]:
            private_channel = guild.get_channel(PRIVATE_CHANNEL_IDS[boss_name])
            try:
                overwrite = discord.PermissionOverwrite()
                overwrite.view_channel=False
                await private_channel.set_permissions(guild.default_role, overwrite=overwrite)
                
            except Exception as e:
                await owner.send("Failed to hide {}: {}".format(boss_name, e))
        """

        for boss_name in setup_json[game_mode]:
            private_channel = guild.get_channel(PRIVATE_CHANNEL_IDS[boss_name])
            public_channel = guild.get_channel(PUBLIC_CHANNEL_IDS[boss_name])
            
            try:
                overwrite = discord.PermissionOverwrite()
                overwrite.create_public_threads = False
                overwrite.create_private_threads = False
                
                if boss_name == today_boss or boss_name == tomorrow_boss:
                    overwrite.view_channel=True
                else:
                    overwrite.view_channel=False
                    
                await public_channel.set_permissions(guild.default_role, overwrite=overwrite)
                
                overwrite.send_messages=False
                await private_channel.set_permissions(guild.default_role, overwrite=overwrite)
                
                """if overwrite.view_channel == False:
                    overwrite.view_channel = None
                    
                overwrite.send_messages=False
                chef_role = guild.get_role(1332134942787764284)
                await private_channel.set_permissions(chef_role, overwrite=overwrite)
                
                overwrite.send_messages=True
                for role_id in WAITER_ROLE_IDS:
                    role = guild.get_role(role_id)
                    await private_channel.set_permissions(role, overwrite=overwrite)"""
                
            except Exception as e:
                await owner.send("Failed to update {}: {}".format(boss_name, e))