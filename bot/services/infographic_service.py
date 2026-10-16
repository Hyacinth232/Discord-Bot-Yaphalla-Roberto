"""Service for managing Yaphalla's infographic links."""

from bot.core.utils import datetime_now, replace_emojis
from bot.database.database import Database


class InfographicService:
    """Stores infographic text (usually image links) by key and formats it for Discord."""

    def __init__(self, db: Database):
        """Initialize infographic service with database connection."""
        self.db = db

    async def get(self, key: str) -> str | None:
        """Return the formatted infographic for a key, or None if it has never been set."""
        value = await self.db.get_image_link(key)
        if not value:
            return None
        return "{}\n<t:{}>".format(value.get("text", ""), value.get("timestamp", ""))

    async def set(self, key: str, text: str) -> str:
        """Store new infographic text for a key and return the formatted result."""
        timestamp = int(datetime_now().timestamp())
        await self.db.set_image_link(key, replace_emojis(text), timestamp)
        return await self.get(key)
