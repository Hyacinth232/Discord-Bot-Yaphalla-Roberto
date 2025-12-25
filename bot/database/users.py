from bot.core.enum_classes import Tile
from bot.database.database import Database


class Users:
    """User formation management with transient in-memory state."""
    def __init__(self):
        """Initialize Users with database connection."""
        self.db = Database()
        self.transient_users = {}
        
    def formation_to_int(self, user_id: int) -> dict[str, dict]:
        """Convert formation keys from string to integer."""
        formation = self.db.get_curr_formation(user_id)
        units = {int(key): value for key, value in formation['units'].items()}
        artifacts = {int(key): value for key, value in formation['artifacts'].items()}
        
        return {'units': units, 'artifacts': artifacts, 'map': formation['map']}
    
    def formation_to_str(self, user_id: int) -> tuple[dict[str, str], dict[str, str], str]:
        """Convert formation keys from integer to string."""
        formation = self.transient_users[user_id]['formation']
        units = {str(key): value for key, value in formation['units'].items()}
        artifacts = {str(key): value for key, value in formation['artifacts'].items()}
        return units, artifacts, formation['map']
        
    def initialize_user(self, user_id: int):
        """Load user data into transient cache if not already loaded."""
        if user_id not in self.transient_users:
            self.db.initialize_user(user_id)
            
            name = self.db.get_curr_name(user_id)
            formation = self.formation_to_int(user_id)
            settings = self.db.get_settings(user_id)
            base_hexes = self.db.get_base_hexes(user_id)
            
            self.transient_users[user_id] = {
                'name': name,
                'formation': formation,
                'settings': settings,
                'base_hexes': base_hexes,
                'saved': True
            }
            
    def add_formation(self, user_id: int, name: str) -> bool:
        units, artifacts, map_name = self.formation_to_str(user_id)
        success = self.db.add_formation(user_id, map_name, units, artifacts, name)
        
        if success:
            self.transient_users[user_id]['name'] = name
            self.save(user_id)
            return True
        
        return False
    
    def update_formation(self, user_id: int) -> bool:
        units, artifacts, map_name = self.formation_to_str(user_id)
        new_name = self.transient_users[user_id]['name']
        old_name = self.db.get_curr_name(user_id)
        success1 = self.db.rename_formation(user_id, old_name, new_name)
        success2 = self.db.update_formation(user_id, map_name, units, artifacts, new_name)
        if success1 or success2:
            self.save(user_id)
            return True
        return False
    
    def overwrite_formation(self, user_id: int, name: str) -> bool:
        units, artifacts, map_name = self.formation_to_str(user_id)
        success = self.db.update_formation(user_id, map_name, units, artifacts, name)
        if success:
            self.transient_users[user_id]['name'] = name
            self.save(user_id)
            return True
        return False
    
    def delete_formation(self, user_id: int, name: str) -> bool:
        return self.db.delete_formation(user_id, name)
    
    def switch_formation(self, user_id: int, name: str) -> bool:
        if self.db.set_curr_formation(user_id, name):
            name = self.db.get_curr_name(user_id)
            formation = self.formation_to_int(user_id)
            
            self.transient_users[user_id]['name'] = name
            self.transient_users[user_id]['formation'] = formation
            self.save(user_id)
            return True
        return False
    
    def rename_formation(self, user_id: int, old_name: str, new_name: str) -> bool:
        curr = False
        if old_name == self.get_name(user_id):
            curr = True
            old_name = self.db.get_curr_name(user_id)
            
        success = self.db.delete_formation(user_id, new_name)
        success = self.db.rename_formation(user_id, old_name, new_name)
        
        if success and curr:
            self.transient_users[user_id]['name'] = new_name
            
        return success

    def name_to_index(self, user_id: int, name: str, tile_type: Tile) -> int:
        """Get index position of unit/artifact by name."""
        idx_lst = [idx for idx, value in self.transient_users[user_id]['formation'][str(tile_type)].items() if value == name]
        if idx_lst:
            return idx_lst[0]

        return 0
    
    def mirror_formation(self, user_id: int) -> dict[str, int]:
        """Mirror formation horizontally by swapping unit positions."""
        units = self.transient_users[user_id]['formation']['units']
        mirror_map = {
            1: 2, 2: 1,
            3: 5, 4: 4, 5: 3,
            6: 7, 7: 6,
            8: 10, 9: 9, 10: 8,
            11: 12, 12: 11,
            13: 13
        }
        self.transient_users[user_id]['formation']['units'] = {mirror_map.get(idx, idx): name for idx, name in units.items()}
        self.unsave(user_id)

    def set_hex(self, user_id: int, name: str, idx: int, tile_type: Tile) -> str:
        """Set unit/artifact at specified index position."""
        self.transient_users[user_id]['formation'][str(tile_type)][idx] = name
        self.unsave(user_id)
        return name

    def pop_hex(self, user_id: int, idx: int, tile_type: Tile) -> str:
        """Remove and return unit/artifact at specified index."""
        if idx in self.transient_users[user_id]['formation'][str(tile_type)]:
            name = self.transient_users[user_id]['formation'][str(tile_type)].pop(idx)
            self.unsave(user_id)
            return name
        return None
    
    def swap_hexes(self, user_id: str, src: int, dst: int, tile_type: Tile) -> list[str]:
        """Swap two units/artifacts at specified indices."""
        names = []

        name1 = self.pop_hex(user_id, src, tile_type)
        if name1: names.append(name1)

        name2 = self.pop_hex(user_id, dst, tile_type)
        if name2:
            names.append(name2)
            self.set_hex(user_id, name2, src, tile_type)

        if name1:
            self.set_hex(user_id, name1, dst, tile_type)
        
        return names
    
    def clear_formation(self, user_id: int):
        """Clear all units and artifacts from formation."""
        self.transient_users[user_id]['formation']['units'] = {}
        self.transient_users[user_id]['formation']['artifacts'] = {}
        self.unsave(user_id)

    def get_units(self, user_id: int) -> dict[int, str]:
        """Get all units in formation."""
        return self.transient_users[user_id]['formation']['units']
    
    def get_artifacts(self, user_id: int) -> dict[int, str]:
        """Get all artifacts in formation."""
        return self.transient_users[user_id]['formation']['artifacts']
    
    def set_map(self, user_id: int, arena: str):
        """Set formation map/arena."""
        self.transient_users[user_id]['formation']['map'] = arena
        self.unsave(user_id)
    
    def get_map(self, user_id: int) -> str:
        """Get current formation map/arena."""
        return self.transient_users[user_id]['formation']['map']
        
    def set_name(self, user_id: int, name: str):
        """Set formation name."""
        self.transient_users[user_id]['name'] = name
        self.unsave(user_id)
    
    def get_name(self, user_id: int) -> str:
        """Get current formation name."""
        return self.transient_users[user_id]['name']
    
    def update_settings(self, user_id: int, key: str, value: bool):
        """Update user display settings."""
        if key == 'make_transparent':
            self.db.update_settings(user_id=user_id, make_transparent=value)  
        elif key == 'show_numbers':
            self.db.update_settings(user_id=user_id, show_numbers=value)
        elif key == 'show_title':
            self.db.update_settings(user_id=user_id, show_title=value)
            
        self.transient_users[user_id]['settings'] = self.db.get_settings(user_id)
    
    def get_settings(self, user_id: int) -> dict[str, bool]:
        """Get user display settings."""
        return self.transient_users[user_id]['settings']
    
    def update_base_hex(self, user_id: int, idx: int, hex_name: str):
        """Update base hex color at specified index."""
        base_hexes = [None, None, None, None]
        base_hexes[idx] = hex_name
        
        self.db.update_base_hexes(user_id,
            base_hexes[0],
            base_hexes[1],
            base_hexes[2],
            base_hexes[3])
        
        self.transient_users[user_id]['base_hexes'][idx] = hex_name
    
    def get_base_hexes(self, user_id: int) -> list[str]:
        """Get base hex colors for user."""
        return self.transient_users[user_id]['base_hexes']
    
    def get_names_list(self, user_id: int):
        """Get list of all saved formation names."""
        return self.db.get_names_list(user_id)
    
    def save(self, user_id: int):
        """Mark formation as saved."""
        self.transient_users[user_id]['saved'] = True
    
    def unsave(self, user_id: int):
        """Mark formation as unsaved."""
        self.transient_users[user_id]['saved'] = False
        
    def get_save_status(self, user_id: int):
        """Check if current formation is saved."""
        return self.transient_users[user_id]['saved']