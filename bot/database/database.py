from pymongo import AsyncMongoClient, ReturnDocument
from pymongo.server_api import ServerApi

DATABASE_NAME = "discord_bot_roberto"


class Database:
    """MongoDB interface for submission counters and infographic links."""

    def __init__(self, mongo_uri: str):
        """Create the client; it connects lazily on the first query."""
        self.client = AsyncMongoClient(mongo_uri, server_api=ServerApi("1"))
        db = self.client[DATABASE_NAME]
        self.counters_db = db["counters"]
        self.images_db = db["image_links"]
        self.images_cache: dict[str, dict | None] = {}

    async def close(self):
        await self.client.close()

    async def increment_counter(self, boss_name: str) -> int:
        """Increment and return counter for boss name."""
        result = await self.counters_db.find_one_and_update(
            {"boss_name": boss_name},
            {"$inc": {"counter": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return result["counter"]

    async def set_image_link(self, key: str, text: str, timestamp: int):
        """Updates or inserts an image link associated with a key."""
        self.images_cache[key] = await self.images_db.find_one_and_update(
            {"key": key},
            {"$set": {"text": text, "timestamp": timestamp}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def get_image_link(self, key: str) -> dict | None:
        """Retrieves an image link by key."""
        if key not in self.images_cache:
            self.images_cache[key] = await self.images_db.find_one({"key": key})
        return self.images_cache[key]
