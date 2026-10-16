"""WebP image conversion utilities."""

import io
import os

from PIL import Image

MIN_QUALITY = 20
MAX_QUALITY = 100
DEFAULT_QUALITY = 80


def convert_to_webp(
    image_bytes: bytes, filename: str, quality: int = DEFAULT_QUALITY, lossless: bool = False
) -> tuple[io.BytesIO, str]:
    """
    Convert image bytes to WEBP format.

    Args:
        image_bytes: Raw image data
        filename: Original filename
        quality: Quality setting for WEBP (20-100)
        lossless: Whether to use lossless compression

    Returns:
        Tuple of (output_buffer, output_filename)

    Raises:
        PIL.UnidentifiedImageError: If the bytes are not an image Pillow can read
    """
    quality = max(MIN_QUALITY, min(quality, MAX_QUALITY))

    with Image.open(io.BytesIO(image_bytes)) as img:
        output_buffer = io.BytesIO()
        img.convert("RGBA").save(output_buffer, format="WEBP", lossless=lossless, quality=quality)
        output_buffer.seek(0)

    base_filename, _ = os.path.splitext(filename)
    return output_buffer, base_filename + ".webp"
