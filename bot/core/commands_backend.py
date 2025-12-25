from bot.core.constants import ARENA_DICT, ARTIFACTS, FILLS, LINES, MAPS, UNITS
from bot.core.enum_classes import Tile
from bot.core.utils import get_emoji, split_input, translate_name
from bot.database.users import Users
from bot.image.image_maker import Image_Maker


def valid_index(idx: int) -> bool:
    """Check if index is valid for unit/artifact placement."""
    return idx != 0 and idx > -4 and idx < 18

def validate_arena(arena: str) -> str:
    """Validate arena name against known maps."""
    if not arena:
        return None
    
    if arena in MAPS:
        return arena
    
    return None

class Commands_Backend:
    """Backend business logic for formation management operations."""
    def __init__(self):
        """Initialize backend with Users instance."""
        self.users = Users()
    
    def __translate_idx(self, user_id: int, idx: str) -> tuple[Tile, int]:
        """Translate index string to tile type and numeric index."""
        if not idx:
            print("What happened here???")
            return
        
        if idx[0] == '-' or idx[0].isdigit():
            try:
                idx = int(idx)
                tile_type = Tile.get_idx_type(idx)
                return tile_type, idx
            except:
                return Tile.OTHER, None
            
        if len(idx) < 3 and idx[0].lower() == "a":
            if len(idx) < 2 or idx[1] == '1':
                return Tile.ARTIFACT, -1
            if idx[1] == '2':
                return Tile.ARTIFACT, -2
            if idx[1] == '3':
                return Tile.ARTIFACT, -3
        
        name = translate_name(idx)
        tile_type = Tile.get_name_type(name)
        if tile_type == Tile.OTHER:
            return Tile.OTHER, None
        
        idx = self.users.name_to_index(user_id, name, tile_type)
        idx = tile_type.convert_idx(idx)
        return Tile.get_idx_type(idx), idx
    
    def __add_one(self, user_id: int, name: str, idx: str):
        """Add one unit/artifact to formation at specified index."""
        name = translate_name(name)
        """
        name_tile_type = Tile.get_name_type(name)
        idx = self.users.name_to_index(user_id, name, name_tile_type)
        if str(idx) != name:
            # Character already exists in formation
            return None
        """
        if name not in UNITS and name not in ARTIFACTS:
            return None
        
        tile_type = Tile.get_idx_type(idx)
        if Tile.get_name_type(name) != tile_type:
            return None
        
        if not valid_index(idx):
            return None
        
        return self.users.set_hex(user_id, name, tile_type.convert_idx(idx), tile_type)
        
    def __add_str(self, user_id: int, name: str, idx: str) -> str:
        """Add unit/artifact using string index."""
        tile_type, idx = self.__translate_idx(user_id, idx)
        return self.__add_one(user_id, name, idx)
    
    def __remove_single(self, user_id: int, idx: str) -> str:
        """Remove single unit/artifact from formation by index."""
        tile_type, idx = self.__translate_idx(user_id, idx)
        
        if tile_type == Tile.OTHER or not valid_index(idx):
            return None

        name = self.users.pop_hex(user_id, tile_type.convert_idx(idx), tile_type)
        return name
    
    def __swap_pair(self, user_id: int, src: str, dst: str) -> list[str]:
        """Swap two units/artifacts in formation."""
        src_tile_type, src = self.__translate_idx(user_id, src)
        dst_tile_type, dst = self.__translate_idx(user_id, dst)
        
        if src_tile_type != dst_tile_type or src_tile_type == Tile.OTHER or not valid_index(src) or not valid_index(dst):
            return []
        
        names = self.users.swap_hexes(
            user_id,
            src_tile_type.convert_idx(src),
            src_tile_type.convert_idx(dst),
            src_tile_type)
        
        return names
    
    def add_one(self, user_id: int, name: str, idx: int) -> tuple[str, str]:
        """Add one unit/artifact and return updated formation image."""
        self.initialize_user(user_id)
        name == self.__add_one(user_id, name, idx)
        if name:
            return name, self.show_image(user_id)
        return None, None
    
    def remove_one(self, user_id: int, name: str) -> tuple[str, str]:
        """Remove one unit/artifact and return updated formation image."""
        self.initialize_user(user_id)
        name = self.__remove_single(user_id, name)
        if name:
            return name, self.show_image(user_id)
        return None, None
    
    def swap_pair(self, user_id: int, name1: str, name2: str) -> tuple[list[str], str]:
        """Swap two units/artifacts and return updated formation image."""
        self.initialize_user(user_id)
        names = self.__swap_pair(user_id, name1, name2)
        if names:
            return names, self.show_image(user_id)
        return [], None
    
    def move_one(self, user_id: int, name: str, idx: int) -> tuple[str, str]:
        """Move unit/artifact to new position and return updated formation image."""
        self.initialize_user(user_id)
        name = self.__remove_single(user_id, name)
        if not name:
            return None, None
        
        name = self.__add_one(user_id, name, idx)
        if name:
            return name, self.show_image(user_id)
        return None, None
    
    def mirror_formation(self, user_id: int):
        """Mirror formation horizontally and return updated image."""
        self.initialize_user(user_id)
        self.users.mirror_formation(user_id)
        return self.show_image(user_id)
    
    def show_image(self, user_id: int, is_private=True) -> str:
        """Generate and return formation image filename."""
        self.initialize_user(user_id)
        settings = self.users.get_settings(user_id)
        base_hexes = self.users.get_base_hexes(user_id)
        
        arena = self.users.get_map(user_id)
        name = self.users.get_name(user_id)
        
        units = self.users.get_units(user_id)
        artifacts = self.users.get_artifacts(user_id)
        
        talent_obj = self.users.db.get_image_link("talents")
        talent = "True" == talent_obj.get('text', '')
        
        with Image_Maker(user_id, base_hexes, settings, arena, is_private, 3 in artifacts, talent) as img_maker:
            file_name = img_maker.generate_image(name, units, artifacts)
        
        return file_name
    
    def name_to_emoji(self, name: str) -> str | None:
        """Convert unit/artifact name to Discord emoji string."""
        name = translate_name(name)
        if name in ARTIFACTS or name in UNITS:
            return get_emoji(name)
        return None
    
    def initialize_user(self, user_id: int):
        """Initialize user data if not already loaded."""
        self.users.initialize_user(user_id)
        
    def clear_user(self, user_id: int):
        """Clear user's formation and return updated image."""
        self.initialize_user(user_id)
        self.users.clear_formation(user_id)
        return self.show_image(user_id)
    
    def set_base_hex(self, user_id: int, idx: int, hex_name: str) -> str | None:
        """Set base hex fill/outline and return updated image."""
        self.initialize_user(user_id)
        if (idx % 2 == 0 and hex_name in FILLS) or (idx % 2 == 1 and hex_name in LINES):
            self.users.update_base_hex(user_id, idx, hex_name)
            return self.show_image(user_id)
        return None

    def set_settings(self, user_id: int, key: str, value: bool) -> str:
        """Update user settings and return updated image."""
        self.initialize_user(user_id)
        self.users.update_settings(user_id, key, value)
        return self.show_image(user_id)
        
    def set_name(self, user_id: int, name: str) -> str | None:
        """Set formation name."""
        self.initialize_user(user_id)
        if name:
            self.users.set_name(user_id, name)
            return name
        return None
    
    def get_name(self, user_id: int) -> str:
        """Get current formation name."""
        self.initialize_user(user_id)
        return self.users.get_name(user_id)
        
    def set_map(self, user_id: int, arena: str) -> tuple[str, str]:
        """Set formation map and return updated image."""
        self.initialize_user(user_id)
        arena = translate_name(arena, ARENA_DICT)
        arena = validate_arena(arena)
        
        if arena:
            self.users.set_map(user_id, arena)
            return arena, self.show_image(user_id)
        return None, None
    
    def add_list(self, user_id: int, pairs: str) -> tuple[list[str], str]:
        """Add multiple units/artifacts from pairs string and return updated image."""
        self.initialize_user(user_id)
        args = split_input(pairs)
        added_names = []

        if len(args) % 2 != 0:
            added_names.append(self.__add_str(user_id=user_id, name=args[-1], idx="A"))
            args = args[:-1]

        for i in range(0, len(args), 2):
            added_names.append(self.__add_str(user_id=user_id, name=args[i], idx=args[i + 1]))
            
        added_names = [name for name in added_names if name]
        
        if added_names:
            return added_names, self.show_image(user_id)
            
        return [], None
        
    def remove_list(self, user_id: int, names_or_indices: str) -> tuple[list[str], str]:
        """Remove multiple units/artifacts and return updated image."""
        self.initialize_user(user_id)
        removed_names = [self.__remove_single(user_id, idx) for idx in split_input(names_or_indices)]
        removed_names = [name for name in removed_names if name]
        
        if removed_names:
            return removed_names, self.show_image(user_id)
        
        return [], None
    
    def swap_list(self, user_id: int, pairs: str) -> tuple[list[str], str]:
        """Swap multiple pairs of units/artifacts and return updated image."""
        self.users.initialize_user(user_id)
        args = split_input(pairs)
        swapped_names = []

        if len(args) % 2 != 0:
            return swapped_names, None
            
        for i in range(0, len(args), 2):
            swapped_names += self.__swap_pair(user_id, args[i], args[i + 1])
        
        if swapped_names:
            return swapped_names, self.show_image(user_id)
            
        return [], None
    
    def get_save_status(self, user_id: int):
        """Check if current formation has been saved."""
        self.initialize_user(user_id)
        return self.users.get_save_status(user_id)
    
    def get_names_list(self, user_id: int) -> list[str]:
        """Get list of all saved formation names for user."""
        self.initialize_user(user_id)
        return self.users.get_names_list(user_id)
        
    def load_formation(self, user_id: int, name: str) -> tuple[bool, str, str]:
        """Load saved formation by name and return updated image."""
        self.initialize_user(user_id)
        success = self.users.switch_formation(user_id, name)
        if success:
            filename = self.show_image(user_id)
            return True, filename, name
        return False, None, name
    
    def add_formation(self, user_id: int, name: str) -> tuple[bool, str]:
        """Save current formation as new named formation."""
        self.initialize_user(user_id)
        success = self.users.add_formation(user_id, name)
        return success, name
    
    def overwrite_formation(self, user_id: int, name: str) -> tuple[bool, str]:
        """Overwrite existing formation with current formation."""
        self.initialize_user(user_id)
        success = self.users.overwrite_formation(user_id, name)
        return success, name
    
    def update_formation(self, user_id: int) -> tuple[bool, str]:
        """Update current formation with changes."""
        self.initialize_user(user_id)
        success = self.users.update_formation(user_id)
        return success, self.users.get_name(user_id)
    
    def delete_formation(self, user_id: int, name: str) -> bool:
        """Delete saved formation by name."""
        self.initialize_user(user_id)
        return self.users.delete_formation(user_id, name), name
    
    def rename_other_formation(self, user_id: int, old_name: str, new_name: str) -> tuple[bool, str]:
        """Rename saved formation."""
        self.initialize_user(user_id)
        success = self.users.rename_formation(user_id, old_name, new_name)
        return success, new_name