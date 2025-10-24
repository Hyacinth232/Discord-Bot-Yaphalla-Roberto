import os

import pygame

from constants import HEX_CATEGORIES
from hex import Hex

HEXES_FOLDER = "Hexes"
ICON_PATH = "icon.png"
YAP_PATH = "Yap.png"

class Image_Loader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print("Created Image Maker Instance")
            cls._instance = super().__new__(cls)
            cls._instance.load_tiles(HEXES_FOLDER)
            cls._instance.load_icon(ICON_PATH)
            cls._instance.load_yap(YAP_PATH)
        return cls._instance
    
    def load_tiles(self, hexes_folder: str) -> dict:
        self.tiles = {}
        for factions in HEX_CATEGORIES.values():
            for faction, names in factions.items():
                for name in names:
                    file_path = os.path.join(hexes_folder, faction, name + ".png")
                    
                    if os.path.exists(file_path):
                        tile = pygame.image.load(file_path)
                        tile = pygame.transform.smoothscale(tile, (Hex.HALF_PNG_WIDTH * 2, Hex.HALF_PNG_HEIGHT * 2))
                        self.tiles[name] = tile
                        # print("Successfully loaded {}.".format(name))
                    else:
                        print("{} does not exist.".format(name))
        
    def load_icon(self, icon_path: str):
        self.icon = pygame.image.load(icon_path)
        self.icon = pygame.transform.smoothscale(self.icon, (Hex.HALF_PNG_WIDTH, Hex.HALF_PNG_WIDTH))
    
    def load_yap(self, yap_path: str):
        self.yap = pygame.image.load(yap_path)
        self.yap = pygame.transform.smoothscale(self.yap, (Hex.HALF_PNG_WIDTH * 2, Hex.HALF_PNG_HEIGHT * 2))