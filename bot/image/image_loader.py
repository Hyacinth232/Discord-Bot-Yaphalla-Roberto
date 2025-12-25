from pathlib import Path

import pygame

from bot.core.constants import (HEX_CATEGORIES, HEXES_FOLDER, ICON_PATH,
                                YAP_PATH)
from bot.image.hex import Hex


class Image_Loader:
    """Singleton class for loading and caching game asset images."""
    _instance = None
    
    def __new__(cls):
        """Create singleton instance and load all assets."""
        if cls._instance is None:
            print("Created Image Maker Instance")
            cls._instance = super().__new__(cls)
            cls._instance.load_tiles(HEXES_FOLDER)
            cls._instance.load_icon(ICON_PATH)
            cls._instance.load_yap(YAP_PATH)
        return cls._instance
    
    def load_tiles(self, hexes_folder: Path) -> dict:
        """Load all hex tile images from folder structure."""
        self.tiles = {}
        for factions in HEX_CATEGORIES.values():
            for faction, names in factions.items():
                for name in names:
                    file_path = hexes_folder / faction / f"{name}.png"
                    
                    if file_path.exists():
                        tile = pygame.image.load(str(file_path))
                        tile = pygame.transform.smoothscale(tile, (Hex.HALF_PNG_WIDTH * 2, Hex.HALF_PNG_HEIGHT * 2))
                        self.tiles[name] = tile
                    else:
                        print("{} does not exist.".format(name))
        
    def load_icon(self, icon_path: Path):
        """Load icon image and scale to appropriate size."""
        self.icon = pygame.image.load(str(icon_path))
        self.icon = pygame.transform.smoothscale(self.icon, (Hex.HALF_PNG_WIDTH, Hex.HALF_PNG_WIDTH))
    
    def load_yap(self, yap_path: Path):
        """Load Yap image and scale to appropriate size."""
        self.yap = pygame.image.load(str(yap_path))
        self.yap = pygame.transform.smoothscale(self.yap, (Hex.HALF_PNG_WIDTH * 2, Hex.HALF_PNG_HEIGHT * 2))