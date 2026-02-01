#!/usr/bin/env python3
"""
Main entry point for the Discord Bot Yaphalla-Roberto
"""
import logging

from bot.core.bot import bot
from bot.core.config import app_settings

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    bot.run(app_settings.bot_token)

