"""Service for generating formation images."""
from bot.database.users import Users
from bot.image.image_maker import Image_Maker
from bot.services.image_service import ImageService


class FormationImageService:
    """Service for generating formation images."""
    def __init__(self, users: Users, image_service: ImageService = None):
        """Initialize formation image service."""
        self.users = users
        self.image_service = image_service or ImageService(users.db)
    
    def generate_formation_image(self, user_id: int, is_private: bool = True) -> str:
        """Generate and return formation image filename."""
        self.users.initialize_user(user_id)
        settings = self.users.get_settings(user_id)
        base_hexes = self.users.get_base_hexes(user_id)
        
        arena = self.users.get_map(user_id)
        name = self.users.get_name(user_id)
        
        units = self.users.get_units(user_id)
        artifacts = self.users.get_artifacts(user_id)
        
        talent_obj = self.image_service.get_image_link("talents")
        talent = "True" == talent_obj.get('text', '')
        
        with Image_Maker(user_id, base_hexes, settings, arena, is_private, 3 in artifacts, talent) as img_maker:
            file_name = img_maker.generate_image(name, units, artifacts)
        
        return file_name

