"""Service for managing submission counters."""
from bot.database.database import Database


class CounterService:
    """Service layer for counter operations."""
    def __init__(self, db: Database = None):
        """Initialize counter service with database connection."""
        self.db = db or Database()
    
    async def increment(self, boss_name: str) -> int:
        """Increment and return counter for boss name."""
        return await self.db.increment_counter(boss_name)

