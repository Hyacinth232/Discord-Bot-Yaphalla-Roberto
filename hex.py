import math


class Hex:
    hex_to_pixel_map = {}
    HALF_PNG_HEIGHT = 50
    HALF_PNG_WIDTH = HALF_PNG_HEIGHT * 9 / 10
    HEX_LENGTH = HALF_PNG_WIDTH * 2 / math.sqrt(3)

    @staticmethod
    def qr_to_xy(q, r) -> tuple[int, int]:
        #s = -q-r
        y = 3/2 * Hex.HEX_LENGTH * q
        x = math.sqrt(3) * Hex.HEX_LENGTH * (q / 2 + r)
        #x = - math.sqrt(3) * Hex.HEX_LENGTH * (q / 2 + s)
        return int(x), int(y)
    
    @staticmethod
    def hex_to_center_pixel(q, r, height):
        x, y = 0, 0
        if (q, r) in Hex.hex_to_pixel_map:
            x, y = Hex.hex_to_pixel_map[(q, r)]
        else:
            x, y = Hex.qr_to_xy(q, r)
            Hex.hex_to_pixel_map[(q, r)] = (x, y)
            
        return x + Hex.HALF_PNG_WIDTH * 6, y + height - Hex.HALF_PNG_HEIGHT * 5.65

    @staticmethod
    def hex_to_corner_pixel(q, r, height):
        x, y = Hex.hex_to_center_pixel(q, r, height)
        return x - Hex.HALF_PNG_WIDTH, y - Hex.HALF_PNG_HEIGHT