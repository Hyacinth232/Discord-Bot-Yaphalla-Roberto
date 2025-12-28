"""Service for managing image links."""
from bot.database.database import Database


class ImageService:
    """Service layer for image link operations."""
    def __init__(self, db: Database = None):
        """Initialize image service with database connection."""
        self.db = db or Database()
    
    def get_image_link(self, key: str) -> dict[str, str | None]:
        """Retrieve image link by key."""
        return self.db.get_image_link(key)
    
    def set_image_link(self, key: str, text: str, timestamp: int):
        """Update or insert image link associated with a key."""
        self.db.set_image_link(key, text, timestamp)

