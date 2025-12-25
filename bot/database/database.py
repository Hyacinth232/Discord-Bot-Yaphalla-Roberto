import os

from pymongo import MongoClient
from pymongo.server_api import ServerApi

from bot.core.constants import MONGO_URI

DEFAULT_HEXES = ["Graveborn-Hex", "Generic-Outline", "Lightbearer-Hex", "Artifact-S3-Outline"]
DEFAULT_MAP = "Arena I"
DEFAULT_NAME = "Untitled"

class Database:
    """MongoDB database interface for user formations and image links."""
    def __init__(self):
        """Initialize MongoDB connection and collections."""
        self.client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
        self.db = self.client['discord_bot_roberto']
        self.users_db = self.db['users']
        self.counters_db = self.db['counters']
        self.users_cache = {}
        
        # For roberto images, unrelated to formations
        self.images_db = self.db['image_links']
        self.images_cache = {}
        
    async def increment_counter(self, boss_name: str) -> int:
        """Increment and return counter for boss name."""
        result = self.counters_db.find_one_and_update(
            {"boss_name": boss_name},
            {"$inc": {"counter": 1}},
            upsert=True,
            return_document=True
        )
        return result["counter"]
        
    def set_image_link(self, key: str, text: str, timestamp: int):
        """Updates or inserts an image link associated with a key."""
        self.images_db.update_one(
            {'key': key},
            {'$set': {
                'text': text,
                'timestamp': timestamp
            }},
            upsert=True
        )
        result = self.images_db.find_one({"key": key})
        self.images_cache[key] = result

    def get_image_link(self, key: str) -> dict[str, str | None]:
        """Retrieves an image link by key."""
        if key not in self.images_cache:
            result = self.images_db.find_one({"key": key})
            self.images_cache[key] = result
            
        return self.images_cache[key]
        
    def __default_user(self, user_id):
        """Create default user document structure."""
        return {
            'user_id': user_id,
            'curr_name': DEFAULT_NAME,
            'formations': {
                DEFAULT_NAME: {
                    'title': '',
                    'subtitle': '',
                    'map': DEFAULT_MAP,
                    'units': {},
                    'artifacts': {}
                }
            },
            'settings': {
                'make_transparent': False,
                'show_numbers': True,
                'show_title': False,
                'title_font_size': 20,
                'subtitle_font_size': 20,
                'number_font_size': 20
            },
            'base_hexes': {
                'unit_fill': DEFAULT_HEXES[0],
                'unit_line': DEFAULT_HEXES[1],
                'arti_fill': DEFAULT_HEXES[2],
                'arti_line': DEFAULT_HEXES[3]
            }
        }
        
    def __pull_from_db(self, user_id: int):
        """Load user document from database into cache."""
        user = self.users_db.find_one({'user_id': user_id})
        self.users_cache[user_id] = user
    
    def __get_user(self, user_id: int):
        """Get user document from cache or database."""
        if user_id not in self.users_cache:
            self.__pull_from_db(user_id)
        return self.users_cache[user_id]
    
    def __update_user(self, user_id: int, key: str, value: any) -> bool:
        """Update user document field in database."""
        result = self.users_db.update_one({'user_id': user_id}, {'$set': {key: value}})
        self.__pull_from_db(user_id)
        
        # TODO: FIX
        #if result.modified_count > 0:
        #self.users_cache[user_id][key] = value
        return True
        #return result.modified_count > 0
        
    def initialize_user(self, user_id: int):
        """Initialize user document if it doesn't exist."""
        if user_id not in self.users_cache:
            self.users_db.update_one({'user_id': user_id}, {'$setOnInsert': self.__default_user(user_id)}, upsert=True)
            self.__pull_from_db(user_id)
            
    def add_formation(self, user_id: int, arena: str, units: dict[str, str], artifacts: dict[str, str], name: str) -> bool:
        """Add new formation if it doesn't already exist."""
        new_formation = { 'map': arena, 'units': units, 'artifacts': artifacts}
        
        # Add formation if it doesn't already exist
        result = self.users_db.update_one(
            {'user_id': user_id, 'formations.{}'.format(name): {'$exists': False}},
            {'$set': {'formations.{}'.format(name): new_formation, 'curr_name': name}}
        )
        
        # TODO: FIX
        #if result.modified_count > 0:
        self.__pull_from_db(user_id)
        return True
        #return result.modified_count > 0

    def update_formation( self, user_id: int, arena: str, units: dict[str, str], artifacts: dict[str, str], name: str) -> bool:
        """Update current formation."""
        new_formation = { 'map': arena, 'units': units, 'artifacts': artifacts}
        
        result = self.users_db.update_one(
            {'user_id': user_id},
            {'$set': {"formations.{}".format(name): new_formation,
                    'curr_name': name}})
        
        self.__pull_from_db(user_id)
        
        # TODO: FIX
        #if result.modified_count > 0:
        return True
    
    def rename_formation(self, user_id: int, old_name: str, new_name: str):
        """Renames formation with old_name to new_name."""
        if old_name == new_name:
            print(old_name)
            print(new_name)
            return False
        
        user = self.__get_user(user_id)
        if old_name not in user['formations'] or new_name in user['formations']:
            return False
        
        update_query = {
            '$rename': {"formations.{}".format(old_name): "formations.{}".format(new_name)},
            '$set': {'curr_name': new_name}
        }
        result = self.users_db.update_one({'user_id': user_id}, update_query)
        # TODO: FIX
        #if result.modified_count > 0:
        self.__pull_from_db(user_id)
        return True
        #return result.modified_count > 0

    def delete_formation(self, user_id: int, name: str) -> bool:
        """Delete formation by name."""
        user = self.__get_user(user_id)
        formations = user['formations']
        
        if name == user['curr_name']:
            return False

        if name in formations:
            del formations[name]
            self.__update_user(user_id, 'formations', formations)
            return True
        
        return False
    
    def get_names_list(self, user_id: int) -> list[str]:
        """Get list of all formation names for user."""
        user = self.__get_user(user_id)
        return [name for name in user['formations']]

    def set_curr_formation(self, user_id: int, name: str) -> bool:
        """Set current formation by name."""
        user = self.__get_user(user_id)
        if name in user['formations']:
            self.__update_user(user_id, 'curr_name', name)
            return True
        return False
    
    def get_curr_formation(self, user_id: int) -> bool:
        """Get current formation document."""
        user = self.__get_user(user_id)
        curr_name = user['curr_name']
        return user['formations'][curr_name]
    
    def get_curr_name(self, user_id: int) -> dict:
        """Get current formation name."""
        user = self.__get_user(user_id)
        return user['curr_name']

    def update_settings(self, user_id: int, make_transparent: bool=None, show_numbers: bool=None, show_title: bool=None):
        """Update user display settings."""
        user = self.__get_user(user_id)
        
        new_settings = user['settings']
        if make_transparent is not None:
            new_settings['make_transparent'] = make_transparent
        if show_numbers is not None:
            new_settings['show_numbers'] = show_numbers
        if show_title is not None:
            new_settings['show_title'] = show_title

        self.__update_user(user_id, 'settings', new_settings)
        
    def get_settings(self, user_id: int) ->dict[str, bool]:
        """Get user display settings."""
        user = self.__get_user(user_id)
        return user['settings']
        
    def update_base_hexes(
        self, user_id: int,
        unit_fill: str=None, unit_line: str=None,
        arti_fill: str=None, arti_line: str=None):
        """Update base hex colors for user."""
        user = self.__get_user(user_id)
        
        new_base_hexes = user['base_hexes']
        if unit_fill is not None:
            new_base_hexes['unit_fill'] = unit_fill
        if unit_line is not None:
            new_base_hexes['unit_line'] = unit_line
        if arti_fill is not None:
            new_base_hexes['arti_fill'] = arti_fill
        if arti_line is not None:
            new_base_hexes['arti_line'] = arti_line
            
        self.__update_user(user_id, 'base_hexes', new_base_hexes)
    
    def get_base_hexes(self, user_id: int) -> dict[str, str]:
        """Get base hex colors for user."""
        user = self.__get_user(user_id)
        return list(user['base_hexes'].values())



