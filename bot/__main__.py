"""Entry point: python -m bot"""

import asyncio
import contextlib
import logging
import signal

import discord

from bot.core.client import Roberto
from bot.core.config import app_settings


async def main():
    async with Roberto() as bot:
        # Heroku stops dynos with SIGTERM; close the gateway connection and database cleanly
        asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(bot.close()))
        await bot.start(app_settings.bot_token)


if __name__ == "__main__":
    discord.utils.setup_logging(level=logging.INFO, root=True)
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
