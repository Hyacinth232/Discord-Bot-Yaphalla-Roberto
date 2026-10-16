"""
Damage number extraction from screenshots using pytesseract.
"""
import io
import re
import subprocess
from typing import Optional

import cv2
#import easyocr
import numpy as np
import pytesseract
from PIL import Image

THIN_SPACE = "\u2009"
NBSP = "\u00A0"

FULLWIDTH_MAP = str.maketrans(
    "０１２３４５６７８９－−‒–—",
    "0123456789-----"
)

UNIT_MULTIPLIERS = {
    # Western
    "K": 1_000,
    "M": 1_000_000,
    "B": 1_000_000_000,
    "T": 1_000_000_000_000,
    # Japanese / Chinese
    "万": 10_000,
    "萬": 10_000,
    "億": 100_000_000,
    "亿": 100_000_000,
    "兆": 1_000_000_000_000,
    # Korean
    "만": 10_000,
    "억": 100_000_000,
    "조": 1_000_000_000_000,
}

# One token that is only a unit
UNIT_TOKEN_RE = re.compile(r"^(?:K|M|B|T|万|萬|億|亿|兆|만|억|조)$", re.IGNORECASE)

# A numeric token that might include separators
NUM_TOKEN_RE = re.compile(r"^[\d][\d,\.\s'']*$")

# Inline number+unit, like 8756億, 1.2M, 10万, 10억
INLINE_NUM_UNIT_RE = re.compile(
    r"^(?P<num>[\d][\d,\.\s'']*([.,]\d+)?)\s*(?P<unit>K|M|B|T|万|萬|億|亿|兆|만|억|조)$",
    re.IGNORECASE
)


def get_all_tesseract_langs(fallback="osd+eng"):
    try:
        out = subprocess.check_output(
            ["tesseract", "--list-langs"],
            text=True,
            stderr=subprocess.STDOUT
        )
        langs = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("list of available languages"):
                continue
            langs.append(line)

        if langs:
            if "osd" in langs:
                langs.remove("osd")
                langs.insert(0, "osd")
            return "+".join(langs)
    except Exception:
        pass

    return fallback


def to_ascii_digits(s: str) -> str:
    """Convert fullwidth digits to ASCII."""
    return (s or "").translate(FULLWIDTH_MAP)


def parse_localized_number(num_str: str) -> float:
    """
    Parses localized numeric strings into float.
    
    Handles:
    - 1,234.56
    - 1.234,56
    - 12 345,6 (space/NBSP/thin space)
    - 9'876.5 (apostrophe thousands)
    - fullwidth digits
    """
    s = to_ascii_digits(num_str).strip()
    s = s.replace(NBSP, " ").replace(THIN_SPACE, " ")
    s = re.sub(r"\s+", " ", s)
    s = s.replace("'", "'").replace("`", "'").strip()
    
    m = re.match(r"^([+-])?\s*(.*)$", s)
    sign = -1.0 if m and m.group(1) == "-" else 1.0
    s = m.group(2) if m else s
    
    s = s.replace(" ", "").replace("'", "")
    if not s:
        raise ValueError("empty numeric string")
    
    comma_count = s.count(",")
    dot_count = s.count(".")
    
    if comma_count > 0 and dot_count > 0:
        # Both exist: last separator is decimal
        if s.rindex(",") > s.rindex("."):
            # Comma is decimal: 1.234,56
            s = s.replace(".", "").replace(",", ".")
        else:
            # Dot is decimal: 1,234.56
            s = s.replace(",", "")
    elif comma_count > 0:
        # Only comma: heuristic based on digits after
        parts = s.split(",", 1)
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely decimal: 123,45
            s = s.replace(",", ".")
        else:
            # Likely thousands: 1,234
            s = s.replace(",", "")
    elif dot_count > 0:
        # Only dot: heuristic based on digits after
        parts = s.split(".", 1)
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely decimal: 123.45
            pass  # Keep as is
        else:
            # Likely thousands: 1.234
            s = s.replace(".", "")
    
    try:
        return sign * float(s)
    except ValueError:
        raise ValueError(f"could not parse as number: {num_str}")


def parse_damage_text(text: str) -> Optional[float]:
    """
    Parse damage text and return numeric value.
    
    Handles formats like:
    - "1234567"
    - "1.2M"
    - "8756億"
    - "10万"
    """
    if not text:
        return None
    
    text = text.strip()
    
    # Try inline number+unit first
    m = INLINE_NUM_UNIT_RE.match(text)
    if m:
        num_str = m.group("num")
        unit = m.group("unit")
        try:
            base_num = parse_localized_number(num_str)
            multiplier = UNIT_MULTIPLIERS.get(unit.upper() if unit.isalpha() else unit, 1)
            return base_num * multiplier
        except ValueError:
            pass
    
    # Try pure number
    if NUM_TOKEN_RE.match(text):
        try:
            return parse_localized_number(text)
        except ValueError:
            pass
    
    return None


class DamageExtractor:
    """Extract damage numbers from screenshots."""
    
    def __init__(self, languages: list = None):
        """
        """
        if languages is None:
            # languages = ['en']
            languages = get_all_tesseract_langs()
        
        # self.reader = easyocr.Reader(languages, gpu=False)
        self.languages = languages
    
    def extract_damage(self, image_bytes: bytes) -> list[dict]:
        """
        Extract damage numbers from image bytes.
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            List of dictionaries with keys:
            - 'text': Detected text
            - 'value': Parsed numeric value (None if parsing failed)
            - 'confidence': OCR confidence score (0.0-1.0)
            - 'bbox': Bounding box coordinates as list of 4 points
        """
        # Convert bytes to numpy array
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return []
        
        #results = self.reader.readtext(image)
        
        # Convert to PIL Image for pytesseract
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Run OCR with detailed data
        data = pytesseract.image_to_data(
            pil_image,
            lang=self.languages,
            output_type=pytesseract.Output.DICT,
            config='--psm 6'  # Assume uniform block of text
        )
        
        damage_results = []
        """for (bbox, text, confidence) in results:
            value = parse_damage_text(text)
            damage_results.append({
                'text': text,
                'value': value,
                'confidence': confidence,
                'bbox': bbox
            })
        return damage_results
        """
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
            
            # Skip empty text or very low confidence
            if not text or conf < 30:
                continue
            
            # Parse the text to extract damage value
            value = parse_damage_text(text)
            
            # Get bounding box
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
            
            damage_results.append({
                'text': text,
                'value': value,
                'confidence': conf / 100.0,  # Convert to 0-1 scale
                'bbox': bbox
            })
        
        return damage_results
        
        
    def extract_largest_damage(self, image_bytes: bytes) -> Optional[float]:
        """
        Extract the largest damage number from image.
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            Largest parsed damage value, or None if none found
        """
        results = self.extract_damage(image_bytes)
        
        valid_values = [r['value'] for r in results if r['value'] is not None]
        if not valid_values:
            return None
        
        return max(valid_values)
    
    def extract_all_damage_values(self, image_bytes: bytes) -> list[float]:
        """
        Extract all valid damage numbers from image.
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            List of all parsed damage values
        """
        results = self.extract_damage(image_bytes)
        return [r['value'] for r in results if r['value'] is not None]

