import io
import os

import discord
from discord.ext import commands, tasks
from PIL import Image

from bot.core.commands_backend import Commands_Backend
from bot.core.commands_frontend import Commands_Frontend
from bot.core.constants import (ADMIN_MOD_ROLE_IDS, ALL_VALID_NAMES,
                                AMARYLLIS_ID, ARTIFACTS, BOT_TOKEN, DR, FILLS,
                                IMAGE_KEYS, LINES, MAPS, PL,
                                PUBLIC_CHANNEL_IDS, ROBERTO_ID, RR, SERVER_ID,
                                UNITS, USAGE, WAITER_ROLE_IDS)
from bot.database.database import Database
from bot.database.users import Users
from bot.services.counter_service import CounterService
from bot.services.formation_image_service import FormationImageService
from bot.services.image_service import ImageService

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

# Initialize singletons - dependency injection setup
_db = Database()
_image_service = ImageService(_db)
_counter_service = CounterService(_db)
_users = Users(_db, _image_service)
_formation_image_service = FormationImageService(_users, _image_service)
_commands_backend = Commands_Backend(_users, _formation_image_service, _counter_service)

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")
commands_frontend = Commands_Frontend(bot, _commands_backend)

@bot.event
async def on_ready():
    """Initialize bot on startup."""
    print(bot.user)
    
    guild = discord.Object(id=SERVER_ID)

    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    await bot.tree.sync()

    owner = await bot.fetch_user(AMARYLLIS_ID)
    if owner: await owner.send(", ".join([guild.name for guild in bot.guilds]))
    
    rotate_channels.start()

### AUTOCOMPLETES ###
async def all_name_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for all valid unit/artifact names."""
    return [discord.app_commands.Choice(name=name, value=name) for name in ALL_VALID_NAMES
            if name.lower().startswith(current.lower())][:25]

async def units_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for unit names."""
    return [discord.app_commands.Choice(name=name, value=name) for name in UNITS
            if name.lower().startswith(current.lower())][:25]

async def artifacts_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for artifact names."""
    return [discord.app_commands.Choice(name=name, value=name) for name in ARTIFACTS
            if name.lower().startswith(current.lower())][:25]
    
async def set_map_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for map/arena names."""
    return [discord.app_commands.Choice(name=map, value=map) for map in MAPS
            if len(map) > 2 and current.lower() in map.lower()][:25]

async def formations_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for saved formation names."""
    user_id = interaction.user.id
    return [discord.app_commands.Choice(name=name, value=name) for name in commands_frontend.get_names_list(user_id) if current in name]

async def fills_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for fill hex names."""
    return [discord.app_commands.Choice(name=name, value=name) for name in FILLS + ["None"]
            if name.lower().startswith(current.lower())][:25]
    
async def lines_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for outline hex names."""
    return [discord.app_commands.Choice(name=name, value=name) for name in LINES
            if name.lower().startswith(current.lower())][:25]
    
channel_names_plus_default = list(PUBLIC_CHANNEL_IDS.keys())
channel_names_plus_default.append("DEFAULT")
async def channels_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for channel names."""
    return [discord.app_commands.Choice(name=name, value=name) for name in channel_names_plus_default
            if name.lower().startswith(current.lower())][:25]
    
image_keys = [discord.app_commands.Choice(name=key, value=key) for key in IMAGE_KEYS]
unit_indices = [discord.app_commands.Choice(name=str(idx), value=idx) for idx in range(1, 15)]
artifact_indices = [discord.app_commands.Choice(name='A{}'.format(idx), value=-idx) for idx in range(1, 4)]

tile_types = [discord.app_commands.Choice(name='Artifacts', value="A"), discord.app_commands.Choice(name='Units', value="B")]
#fills = [discord.app_commands.Choice(name=name, value=name) for name in FILLS][:25]
#outlines = [discord.app_commands.Choice(name=name, value=name) for name in LINES][:25]


### LOOP TASK
@tasks.loop(hours=6)
async def rotate_channels():
    """Periodic task to rotate channel permissions."""
    await commands_frontend.rotate_channels(bot)
    
#####################
### HOUSE KEEPING ###
#####################
"""
@bot.tree.command(name="help", description="Show Roberto's list of commands")
async def help_command(interaction: discord.Interaction, show_public: bool=False):
    await interaction.response.send_message(USAGE, ephemeral=not show_public)
"""

@bot.tree.command(name="emoji", description="Shows character with the given name")
@discord.app_commands.autocomplete(name=all_name_autocomplete)
@discord.app_commands.describe(name="Character name")
async def emoji(interaction: discord.Interaction, name: str, show_public: bool=False):
    await commands_frontend.emoji_wrapper(interaction, name, show_public)

@bot.tree.command(name="emojify")
async def charms(interaction: discord.Interaction, text: str):
    await commands_frontend.emojify_wrapper(interaction, text)
    
@bot.tree.command(name="get_timestamp", description="Convert a date/time to a UTC Discord timestamp")
async def get_timestamp(interaction: discord.Interaction, month: int, day: int, year: int=2025, hour: int=0):
    await commands_frontend.get_timestamp(interaction, year, month, day, hour)

@bot.tree.command(name="time_now")
async def time_now(interaction: discord.Interaction):
    await commands_frontend.time_now_wrapper(interaction)
    
##############
### GUIDES ###
##############

def is_admin(interaction: discord.Interaction) -> bool:
    if interaction.guild is None or interaction.guild.id != SERVER_ID:
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    if interaction.user.id == AMARYLLIS_ID:
        return True
    return any(role.id in ADMIN_MOD_ROLE_IDS for role in interaction.user.roles)

def is_waiter(interaction: discord.Interaction) -> bool:
    if interaction.guild is None or interaction.guild.id != SERVER_ID:
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    if interaction.user.id == AMARYLLIS_ID:
        return True
    return any(role.id in WAITER_ROLE_IDS for role in interaction.user.roles)

@bot.tree.command(name="benchmark")
@discord.app_commands.check(is_waiter)
async def benchmark_pls(interaction: discord.Interaction):
    await interaction.response.send_message(
        '<@&1332134991861383390>',
        allowed_mentions=discord.AllowedMentions(roles=True)
    )
    
@bot.command(name='souschef')
async def souschef(ctx: commands.Context):
    channel = ctx.channel
    if channel.id not in PUBLIC_CHANNEL_IDS.values() and channel.id not in [1363693988506243253, 1369228828412612670]: return
    
    content = ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with):].lstrip()
    text = '<@&1348163901149417553> ' + content
    files = []
    for attachment in ctx.message.attachments:
        file_bytes = await attachment.read()
        files.append(discord.File(io.BytesIO(file_bytes), filename=attachment.filename))

    await channel.send(
        text,
        files=files,
        allowed_mentions=discord.AllowedMentions(roles=True)
    )
    
@bot.tree.command(name="yap_update_image")
@discord.app_commands.check(is_waiter)
@discord.app_commands.choices(key=image_keys)
async def yap_update_image(interaction: discord.Interaction, key: discord.app_commands.Choice[str], text: str):
    await commands_frontend.set_image_link(interaction, key.name, text)

@yap_update_image.error
async def admin_update_image_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.CheckFailure):
        await interaction.response.send_message("This command is only available for Yaphalla admins.", ephemeral=True)

@bot.tree.command(name="paragon", description="Show Yaphalla's Paragon Graphic")
async def paragon(interaction: discord.Interaction):
    await commands_frontend.get_image_embed(interaction, 'paragon')
    
@bot.tree.command(name="dream-realm", description="Yaphalla's Dream Realm infographics")
async def dream_realm(interaction: discord.Interaction):
    await commands_frontend.dropdown_wrapper(interaction, DR)
    
@bot.tree.command(name="dr", description="Yaphalla's Dream Realm infographics")
async def dr(interaction: discord.Interaction):
    await commands_frontend.dropdown_wrapper(interaction, DR)
    
@bot.tree.command(name="primal-lord", description="Yaphalla's Primal Lord infographics")
async def primal_lord(interaction: discord.Interaction):
    await commands_frontend.dropdown_wrapper(interaction, PL)
    
@bot.tree.command(name="pl", description="Yaphalla's Primal Lord infographics")
async def pl(interaction: discord.Interaction):
    await commands_frontend.dropdown_wrapper(interaction, PL)

@bot.tree.command(name="charms", description="Show Yaphalla's DR Charms Graphic")
async def charms(interaction: discord.Interaction):
    await commands_frontend.get_image_embed(interaction, 'charms')
"""
@bot.tree.command(name="charms-pvp", description="Show Yaphalla's PvP Charms Graphic")
async def charms(interaction: discord.Interaction):
    await commands_frontend.get_image_embed(interaction, 'charmspvp')
    
@bot.tree.command(name="charmspvp", description="Show Yaphalla's PvP Charms Graphic")
async def charms(interaction: discord.Interaction):
    await commands_frontend.get_image_embed(interaction, 'charmspvp')
    
@bot.tree.command(name="charms-reference", description="V+ Charms Cheat Sheet")
async def charms(interaction: discord.Interaction):
    await commands_frontend.get_image_embed(interaction, 'charms_reference')
    
@bot.tree.command(name="charms-ref", description="V+ Charms Cheat Sheet")
async def charms(interaction: discord.Interaction):
    await commands_frontend.get_image_embed(interaction, 'charms_reference')
"""

@bot.tree.command(name="ravaged-realm", description="Yaphalla's Ravaged Realm infographics")
async def rr(interaction: discord.Interaction):
    await commands_frontend.dropdown_wrapper(interaction, RR)


#########################
### FORMATION BUILDER ###
#########################

### ADD & REMOVE
@bot.tree.command(name="add_list", description="Adds tiles to a formation")
@discord.app_commands.describe(pairs="Pairs of names and indices")
async def add_list_en(interaction: discord.Interaction, pairs: str):
    await commands_frontend.add_wrapper(interaction, pairs)

@bot.tree.command(name="add_unit", description="Add one unit")
@discord.app_commands.autocomplete(unit=units_autocomplete)
@discord.app_commands.choices(idx=unit_indices)
async def add_unit(interaction: discord.Interaction, unit: str, idx: discord.app_commands.Choice[int]):
    await commands_frontend.add_one_wrapper(interaction, unit, idx.value)
    
@bot.tree.command(name="add_artifact", description="Add one artifact")
@discord.app_commands.autocomplete(artifact=artifacts_autocomplete)
@discord.app_commands.choices(idx=artifact_indices)
async def add_artifact(interaction: discord.Interaction, artifact: str, idx: discord.app_commands.Choice[int]=None):
    if idx:
        await commands_frontend.add_one_wrapper(interaction, artifact, idx.value)
    else:
        await commands_frontend.add_one_wrapper(interaction, artifact, -1)

@bot.tree.command(name="remove_list", description="Removes tiles from a formation")
@discord.app_commands.describe(names_or_indices="Names or indices of the characters to remove")
async def remove_list_en(interaction: discord.Interaction, names_or_indices: str):
    await commands_frontend.remove_wrapper(interaction, names_or_indices)
    
### SWAP
@bot.tree.command(name="swap_list", description="Swaps a list of tiles in a formation")
@discord.app_commands.describe(pairs="Pairs of indices to swap")
async def swap_en(interaction: discord.Interaction, pairs: str):
    await commands_frontend.swap_wrapper(interaction, pairs)

@bot.tree.command(name="swap_units", description="Swaps two units")
@discord.app_commands.autocomplete(unit1=units_autocomplete)
@discord.app_commands.autocomplete(unit2=units_autocomplete)
async def swap_units(interaction: discord.Interaction, unit1: str, unit2: str):
    await commands_frontend.swap_pair_wrapper(interaction, unit1, unit2)

@bot.tree.command(name="move_unit", description="Moves one unit to a tile")
@discord.app_commands.choices(idx=unit_indices)
@discord.app_commands.autocomplete(unit=units_autocomplete)
async def move_unit(interaction: discord.Interaction, unit: str, idx: discord.app_commands.Choice[int]):
    await commands_frontend.move_one_wrapper(interaction, unit, idx.value)

@bot.tree.command(name="mirror", description="Mirrors a formation (when map is symmetrical)")
@discord.app_commands.choices()
async def move_unit(interaction: discord.Interaction):
    await commands_frontend.mirror_wrapper(interaction)

### CLEAR
@bot.tree.command(name="clear_formation", description="Clears your current formation")
async def clear_formation(interaction: discord.Interaction):
    await commands_frontend.clear_wrapper(interaction)

### DISPLAY
@bot.tree.command(name="display", description="Display your current formation")
async def display(interaction: discord.Interaction, show_public:bool=False):
    await commands_frontend.display_formation_wrapper(interaction, ephemeral=not show_public, display_mode=True)

@bot.tree.command(name="view", description="View your current formation")
async def view_en(interaction: discord.Interaction, show_public:bool=False):
    await commands_frontend.display_formation_wrapper(interaction, ephemeral=not show_public, display_mode=False)
    
@bot.tree.command(name="see", description="View your current formation")
async def see_en(interaction: discord.Interaction, show_public:bool=False):
    await commands_frontend.display_formation_wrapper(interaction, ephemeral=not show_public, display_mode=False)
    
### CONFIG
@bot.tree.command(name="set_map", description="Sets your current map")
@discord.app_commands.autocomplete(map=set_map_autocomplete)
async def set_map(interaction: discord.Interaction, map: str):
    await commands_frontend.set_map_wrapper(interaction, map)

@bot.tree.command(name="set_name", description="Sets a name for your formation")
async def set_name(interaction: discord.Interaction, name: str):
    await commands_frontend.set_name_wrapper(interaction, name)

### SETTINGS
@bot.tree.command(name="show_title", description="Shows your formation name as the title")
async def show_title(interaction: discord.Interaction, show_title: bool):
    await commands_frontend.show_title_wrapper(interaction, show_title)
    
@bot.tree.command(name="show_numbers", description="Shows or hides tile numbers")
async def show_numbers(interaction: discord.Interaction, show_numbers: bool):
    await commands_frontend.show_numbers_wrapper(interaction, show_numbers)
    
@bot.tree.command(name="make_transparent", description="Makes base tiles transparent or opaque")
async def make_transparent(interaction: discord.Interaction, make_transparent: bool):
    await commands_frontend.make_transparent_wrapper(interaction, make_transparent)

### DATABASE FORMATIONS
@bot.tree.command(name="formation_name", description="Shows name of current formation")
async def current_name(interaction: discord.Interaction):
    await commands_frontend.current_name_wrapper(interaction)
    
@bot.tree.command(name="list_formations", description="Lists all saved formations")
async def list_formations(interaction: discord.Interaction):
    await commands_frontend.list_formations_wrapper(interaction)
    
@bot.tree.command(name="save_formation", description="Saves current formation")
async def save(interaction: discord.Interaction):
    await commands_frontend.save_wrapper(interaction)
    
@bot.tree.command(name="rename_formation", description="Renames current formation")
async def rename(interaction: discord.Interaction, name: str):
    await commands_frontend.rename_wrapper(interaction, name)
    
@bot.tree.command(name="save_as", description="Saves current formation as name")
async def save_as(interaction: discord.Interaction, name: str):
    await commands_frontend.save_as_wrapper(interaction, name)
    
@bot.tree.command(name="load_formation", description="Loads a saved formation")
@discord.app_commands.autocomplete(name=formations_autocomplete)
async def load(interaction: discord.Interaction, name: str):
    await commands_frontend.load_wrapper(interaction, name)

@bot.tree.command(name="delete_formation", description="Deletes a saved formation")
@discord.app_commands.autocomplete(name=formations_autocomplete)
async def delete(interaction: discord.Interaction, name: str):
    await commands_frontend.delete_wrapper(interaction, name)

### BASE HEXES
@bot.tree.command(name="set_base_fill", description="Sets the base hex fill colour")
@discord.app_commands.choices(tile_type=tile_types)
@discord.app_commands.autocomplete(hex=fills_autocomplete)
async def set_base_fill(interaction: discord.Interaction, tile_type: discord.app_commands.Choice[str], 
                        hex: str):
    if tile_type.name == 'Units':
        await commands_frontend.set_base_hex(interaction, 0, hex)
    else:
        await commands_frontend.set_base_hex(interaction, 2, hex)
        
@bot.tree.command(name="set_base_outline", description="Sets the base hex line colour")
@discord.app_commands.choices(tile_type=tile_types)
@discord.app_commands.autocomplete(hex=lines_autocomplete)
async def set_base_outline(interaction: discord.Interaction, tile_type: discord.app_commands.Choice[str], 
                        hex: str):
    if tile_type.name == 'Units':
        await commands_frontend.set_base_hex(interaction, 1, hex)
    else:
        await commands_frontend.set_base_hex(interaction, 3, hex)
        
@bot.tree.command(name="yap_map")
@discord.app_commands.check(is_waiter)
@discord.app_commands.autocomplete(map=set_map_autocomplete)
@discord.app_commands.autocomplete(channel=channels_autocomplete)
async def yap_set_map(interaction: discord.Interaction, channel: str, map: str):
    channel_id  = PUBLIC_CHANNEL_IDS[channel] if channel in PUBLIC_CHANNEL_IDS else ROBERTO_ID
    await commands_frontend.set_map_wrapper(interaction, map=map, user_id=channel_id, save_map=True)

@bot.tree.command(name="yap_base_hex")
@discord.app_commands.check(is_waiter)
@discord.app_commands.autocomplete(fill=fills_autocomplete)
@discord.app_commands.autocomplete(line=lines_autocomplete)
@discord.app_commands.autocomplete(channel=channels_autocomplete)
async def yap_set_base_hex(interaction: discord.Interaction, channel: str, fill: str, line: str):
    channel_id  = PUBLIC_CHANNEL_IDS[channel] if channel in PUBLIC_CHANNEL_IDS else ROBERTO_ID
    make_transparent = fill == "None"
    await commands_frontend.yap_set_base_hex(interaction, fill, line, make_transparent, user_id=channel_id, ephemeral=False)
        
"""
@bot.tree.command(name="yap_fill")
@discord.app_commands.check(is_waiter)
@discord.app_commands.autocomplete(hex=fills_autocomplete)
@discord.app_commands.autocomplete(channel=channels_autocomplete)
async def yap_fill(interaction: discord.Interaction, channel: str, hex: str):
    channel_id  = PUBLIC_CHANNEL_IDS[channel] if channel in PUBLIC_CHANNEL_IDS else ROBERTO_ID
    await commands_frontend.set_base_hex(interaction, 0, hex, user_id=channel_id, ephemeral=False)
        
@bot.tree.command(name="yap_outline")
@discord.app_commands.check(is_waiter)
@discord.app_commands.autocomplete(hex=lines_autocomplete)
@discord.app_commands.autocomplete(channel=channels_autocomplete)
async def yap_outline(interaction: discord.Interaction, channel: str, hex: str):
    channel_id  = PUBLIC_CHANNEL_IDS[channel] if channel in PUBLIC_CHANNEL_IDS else ROBERTO_ID
    await commands_frontend.set_base_hex(interaction, 1, hex, user_id=channel_id, ephemeral=False)
"""

########################
### SUBMIT FORMATION ###
########################
#@bot.tree.context_menu(name="Submit Formation")
#async def submit_message(interaction: discord.Interaction, message: discord.Message):
#    await commands_frontend.modal_submit_message_wrapper(interaction, message)

@bot.tree.context_menu(name="Submit Team w/ Details")
async def submit_form_w_details(interaction: discord.Interaction, message: discord.Message):
    await commands_frontend.context_form_modal_wrapper(interaction, message)

@bot.tree.context_menu(name="Edit & Submit Team")
async def edit_submit_team(interaction: discord.Interaction, message: discord.Message):
    await commands_frontend.context_basic_modal_wrapper(interaction, message)

@bot.tree.context_menu(name="Submit Team")
async def submit_team(interaction: discord.Interaction, message: discord.Message):
    await commands_frontend.context_no_modal_wrapper(interaction, message)
    
@bot.tree.command(name="submit")
async def submit_form(
    interaction: discord.Interaction,
    file1: discord.Attachment,
    file2: discord.Attachment=None,
    file3: discord.Attachment=None,
    file4: discord.Attachment=None,
    file5: discord.Attachment=None
    ):
    attachments = [file1, file2, file3, file4, file5]
    await commands_frontend.command_form_modal_wrapper(interaction, attachments)
    
@bot.command(name="webp")
async def to_webp(ctx: commands.Context, user_quality: int = 80):
    if not ctx.message.reference:
        return
    user_quality = max(20, min(user_quality, 100))
    
    await webp_helper(ctx, user_quality)
    
@bot.command(name="lwebp")
async def to_lwebp(ctx: commands.Context):
    if not ctx.message.reference:
        return
    await webp_helper(ctx, 100, True)

async def webp_helper(ctx: commands.Context, user_quality: int, lossless: bool=False):
    replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    if replied_message.attachments:
        attachment = replied_message.attachments[0]
        
        if attachment.content_type and 'image' in attachment.content_type and attachment.filename.lower().endswith(".png"):
            image_bytes = await attachment.read()
            
            with Image.open(io.BytesIO(image_bytes)).convert("RGBA") as img:
                output_buffer = io.BytesIO()

                filename, _ = os.path.splitext(attachment.filename)
                
                img.save(output_buffer, format="WEBP", lossless=lossless, quality=user_quality)
                output_buffer.seek(0)
                
                await ctx.channel.send(file=discord.File(fp=output_buffer, filename=filename + ".webp"))

@bot.command(name="submit")
async def submit_formation(ctx: commands.Context):
    await commands_frontend.submit_wrapper(ctx)
    
@bot.command(name="collect")
async def collect(ctx: commands.Context, index: int=-1):
    await commands_frontend.collect_wrapper(ctx, index)

### OVERRIDES
@bot.command(name='amaryllis')
async def toggle_manage_channels(ctx: commands.Context):
    owner = await bot.fetch_user(AMARYLLIS_ID)
    guild = bot.get_guild(SERVER_ID)
    
    if guild is None:
        print("Server not found.")
        return

    if ctx.author.id != AMARYLLIS_ID: return
    
    try:
        mod_role = ctx.guild.get_role(1348155560780103701)
        if mod_role is None:
            await owner.send("Role not found.")
            return
        
        perms = mod_role.permissions
        new_state = not perms.manage_channels
        new_state2 = not perms.mention_everyone
        perms.update(manage_channels=new_state)
        perms.update(mention_everyone=new_state2)
        
        await mod_role.edit(permissions=perms)
        await owner.send("Manage Channels perm for {} has been set to {}.".format(mod_role.name, new_state))
        
    except discord.Forbidden:
        await owner.send("No permission to toggle")
    except discord.HTTPException as e:
        await owner.send("Failed: {}".format(e))

bot.run(BOT_TOKEN)