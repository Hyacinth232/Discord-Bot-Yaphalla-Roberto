"""WebP image conversion utilities."""
import io
import os

from PIL import Image


class WebpConverter:
    """Class for converting images to WEBP format."""
    
    @staticmethod
    def convert_to_webp(image_bytes: bytes, filename: str, user_quality: int, lossless: bool = False) -> tuple[io.BytesIO, str]:
        """
        Convert image bytes to WEBP format.
        
        Args:
            image_bytes: Raw image data
            filename: Original filename
            user_quality: Quality setting for WEBP (20-100)
            lossless: Whether to use lossless compression
            
        Returns:
            Tuple of (output_buffer, output_filename)
        """
        with Image.open(io.BytesIO(image_bytes)).convert("RGBA") as img:
            output_buffer = io.BytesIO()

            base_filename, _ = os.path.splitext(filename)
            output_filename = base_filename + ".webp"
            
            img.save(output_buffer, format="WEBP", lossless=lossless, quality=user_quality)
            output_buffer.seek(0)
            
            return output_buffer, output_filename
