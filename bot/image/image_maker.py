import math

import pygame

from bot.core.constants import FONT_PATH, HEX_CATEGORIES, MAPS
from bot.image.hex import Hex
from bot.image.image_loader import Image_Loader

MARGIN = 20
FONT_SIZE = 20

class Image_Maker:
    """Generate formation images using pygame."""
    def __init__(self, user_id: int, base_hexes: list[str], settings: dict[str, bool], arena: str, is_private: bool, test_setting, talent: bool=False):
        """Initialize image maker with user settings and arena configuration."""
        self.loader = Image_Loader()
        self.user_id = user_id
        self.arena = arena
        if self.arena not in MAPS:
            self.arena = "Arena I"
        self.tiles = sorted(MAPS[self.arena]['Tiles'], key=lambda x: (x[0] - x[1], x[0], x[1]), reverse=True)
            
        self.is_private = is_private
        self.show_outline = True
        self.show_fill = not settings['make_transparent']
        self.show_number = settings['show_numbers'] or is_private
        self.show_title = settings['show_title'] # or is_private
        
        self.unit_fill = base_hexes[0]
        self.unit_line = base_hexes[1]
        self.arti_fill = base_hexes[2]
        self.arti_line = base_hexes[3]

        self.width =  MAPS[self.arena]['Width']
        self.height = MAPS[self.arena]['Height']
        
        self.extra_height = 0
        if self.show_title:
            self.height += 50
            self.extra_height = 50
            
        self.test_setting = 15 if test_setting else 0
        self.talent = talent
        
        self.mauler_count = 0
        

    def __enter__(self):
        """Initialize pygame and create surface."""
        pygame.init()
        self.font = pygame.font.Font(str(FONT_PATH), FONT_SIZE)
        self.surface = pygame.Surface((self.width, self.height + self.test_setting), pygame.SRCALPHA)
        self.surface.fill((0, 0, 0, 0))
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up pygame on exit."""
        pygame.quit()
            
    def __draw_yap(self, artifacts):
        """Draw Yap character if certain artifacts are not present."""
        if 2 not in artifacts and 3 not in artifacts:
            x, y = Hex.hex_to_corner_pixel(3, -3, self.height)
            self.surface.blit(self.loader.yap, (x, y))
        """if self.arena == "Arena V - Special":
            self.surface.blit(self.loader.icon, (self.width - Hex.HALF_PNG_WIDTH - MARGIN, self.height - Hex.HALF_PNG_WIDTH - MARGIN))
        else:
            self.surface.blit(self.loader.icon, (self.width - Hex.HALF_PNG_WIDTH - MARGIN, self.extra_height + MARGIN))
        """
        
    def __draw_talents(self):
        """Draw talent indicators based on arena and mauler count."""
        q1, r1, q2, r2 = 0, 0, 0, 0
        
        if self.arena == "Ravaged Realm":
            if self.mauler_count >= 3:
                q1, r1 = self.tiles[-3]
                q2, r2 = self.tiles[-4]
            else:
                q1, r1 = self.tiles[2]
                q2, r2 = self.tiles[3]
        else:
            if self.mauler_count >= 3:
                q1, r1 = self.tiles[-2]
                q2, r2 = self.tiles[-3]
            else:
                q1, r1 = self.tiles[0]
                q2, r2 = self.tiles[1]
        
        x, y = Hex.hex_to_corner_pixel(q1, r1, self.height)
        self.surface.blit(self.loader.tiles["Mythic-Outline"], (x, y))
        
        x, y = Hex.hex_to_corner_pixel(q2, r2, self.height)
        self.surface.blit(self.loader.tiles["Mythic-Outline"], (x, y))
        
    def __draw_text(self, center_x, center_y, text: str):
        """Draw text at specified center coordinates."""
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(center_x, center_y))
        self.surface.blit(text_surface, text_rect.topleft)
        
    def __draw_occupied_tile(self, x, y, name: str):
        """Draw tile with unit/artifact image."""
        self.surface.blit(self.loader.tiles[name], (x, y))
        if not self.show_outline:
            self.surface.blit(self.loader.tiles[self.unit_line], (x, y))
    
    def __draw_blank_tile(self, x, y, blank_fill: str, blank_line: str):
        """Draw empty tile with fill and outline."""
        if self.show_fill:
            self.surface.blit(self.loader.tiles[blank_fill], (x, y))
        self.surface.blit(self.loader.tiles[blank_line], (x, y))

    def __draw_units(self, units: dict[int, str]):
        """Draw all unit tiles on the formation."""
        self.mauler_count = 0
        for idx, (q,r) in enumerate(self.tiles):
            idx += 1
            
            x, y = Hex.hex_to_corner_pixel(q, r, self.height)
            if idx in units:
                self.__draw_occupied_tile(x, y, units[idx])
                if units[idx] in HEX_CATEGORIES['Units']['Mauler']:
                    self.mauler_count += 1
                continue
            
            center_x, center_y = Hex.hex_to_center_pixel(q, r, self.height)
            self.__draw_blank_tile(x, y, self.unit_fill, self.unit_line)
            if self.show_number:
                self.__draw_text(center_x, center_y, str(idx))
            
            # Mauler tiles
            #if (q, r) == (0, -1) or (q, r) == (1, 0):
            #    self.surface.blit(self.loader.tiles["Gold-Artifact-Hex"], (x, y))

    def __draw_artifacts(self, artifacts: dict[int, str]):
        """Draw artifact tiles on the formation."""
        def_x, def_y = Hex.hex_to_corner_pixel(3, -4, self.height)
        def_cx, def_cy = Hex.hex_to_center_pixel(3, -4, self.height)

        for i in range(3):
            x, y = def_x, def_y
            cx, cy = def_cx, def_cy
            
            if 3 in artifacts:
                if i == 0:
                    x += 15 * math.sqrt(3)
                    y += 15
                    cx += 15 * math.sqrt(3)
                    cy += 15
                if i == 1:
                    x += -25
                    y += 25 * math.sqrt(3)
                    cx += -25
                    cy += 25 * math.sqrt(3)
                elif i == 2:
                    x += -15 * math.sqrt(3)
                    y += -15
                    cx += -15 * math.sqrt(3)
                    cy += -15
            
            if 2 in artifacts and 3 not in artifacts:
                if i == 1:
                    x += 15 * math.sqrt(3)
                    y += 15
                    cx += 15 * math.sqrt(3)
                    cy += 15
                elif i == 2:
                    x += -15 * math.sqrt(3)
                    y += -15
                    cx += -15 * math.sqrt(3)
                    cy += -15

            idx = 3 - i
            if idx in artifacts:
                self.__draw_occupied_tile(x, y, artifacts[idx])
                continue
            
            if idx + 1 in artifacts or idx + 2 in artifacts:
                self.__draw_blank_tile(x, y, self.arti_fill, self.arti_line)
                if self.show_number:
                    self.__draw_text(cx, cy, 'A')
        
    def generate_image(self, title, units, artifacts):
        """Generate complete formation image and save to file."""
        if self.show_title:
            self.__draw_text(self.width / 2, FONT_SIZE + MARGIN, title)

        self.__draw_units(units)
        self.__draw_artifacts(artifacts)
        self.__draw_yap(artifacts)
        
        if self.talent:
            self.__draw_talents()
        
        file_name = '{}.png'.format(self.user_id)
        pygame.image.save(self.surface, file_name)

        return file_name