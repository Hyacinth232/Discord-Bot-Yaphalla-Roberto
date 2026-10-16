"""Roberto's bot client: wires up services, loads cogs and syncs application commands."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.config import app_settings, db_settings
from bot.database.database import Database
from bot.services.counter_service import CounterService
from bot.services.infographic_service import InfographicService

logger = logging.getLogger(__name__)

EXTENSIONS = (
    "bot.cogs.submissions",
    "bot.cogs.infographics",
    "bot.cogs.utilities",
    "bot.cogs.staff",
    "bot.cogs.rotation",
)

PERMISSION_DENIED = "You don't have permission to use this command."
GENERIC_ERROR = "Something went wrong. Please try again or contact staff."


class RobertoCommandTree(app_commands.CommandTree):
    """Command tree with a shared error handler for every slash and context menu command."""

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            message = PERMISSION_DENIED
        else:
            command_name = interaction.command.name if interaction.command else "unknown"
            logger.error("Error in command %s", command_name, exc_info=error)
            message = GENERIC_ERROR

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


class Roberto(commands.Bot):
    """Yaphalla's Roberto. Only responds to application commands; there are no prefix commands."""

    def __init__(self):
        super().__init__(
            # commands.Bot requires a prefix, but no prefix commands are registered
            command_prefix=commands.when_mentioned,
            help_command=None,
            intents=discord.Intents.default(),
            tree_cls=RobertoCommandTree,
        )
        self.database = Database(db_settings.mongo_uri)
        self.counter_service = CounterService(self.database)
        self.infographic_service = InfographicService(self.database)

    async def setup_hook(self):
        """Load cogs and sync application commands before connecting to Discord."""
        for extension in EXTENSIONS:
            await self.load_extension(extension)

        # Remove any commands left registered to the server only; all commands are global
        server = discord.Object(id=app_settings.server_id)
        self.tree.clear_commands(guild=server)
        await self.tree.sync(guild=server)

        synced = await self.tree.sync()
        logger.info("Synced %d global application commands", len(synced))

    async def close(self):
        await super().close()
        await self.database.close()

    async def on_ready(self):
        logger.info("Bot %s (ID: %s) started", self.user, self.user.id)
        logger.info("Connected to %d server(s)", len(self.guilds))

        owner = await self.fetch_user(app_settings.amaryllis_id)
        await owner.send(", ".join(guild.name for guild in self.guilds))
