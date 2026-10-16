import io

import discord
import pytest
from PIL import Image, UnidentifiedImageError

from bot.image.webp_converter import convert_to_webp
from bot.ui.embeds import make_embeds


def image_bytes(fmt: str = "PNG", mode: str = "RGBA", color=(255, 0, 0)) -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, (8, 8), color).save(buffer, fmt)
    return buffer.getvalue()


@pytest.mark.parametrize(("fmt", "mode"), [("PNG", "RGBA"), ("JPEG", "RGB")])
def test_converts_to_webp(fmt: str, mode: str):
    buffer, filename = convert_to_webp(image_bytes(fmt, mode), "team.screenshot.png", quality=50)
    assert filename == "team.screenshot.webp"
    assert Image.open(buffer).format == "WEBP"


def test_lossless_webp_keeps_pixels_and_transparency():
    buffer, _ = convert_to_webp(image_bytes(color=(255, 0, 0, 128)), "a.png", lossless=True)
    assert Image.open(buffer).getpixel((0, 0)) == (255, 0, 0, 128)


def test_rejects_non_images():
    with pytest.raises(UnidentifiedImageError):
        convert_to_webp(b"not an image", "a.png")


def test_embeds_show_images_but_not_videos():
    files = [discord.File(io.BytesIO(b""), filename=name) for name in ("img_0.png", "img_1.mp4", "img_2.jpg")]
    embeds = make_embeds("text", "footer", files)

    assert [embed.image.url for embed in embeds] == ["attachment://img_0.png", "attachment://img_2.jpg"]
    assert embeds[0].description == "text"
    assert embeds[0].footer.text == "footer"


def test_embeds_without_files():
    embeds = make_embeds("text", "footer")
    assert len(embeds) == 1
    assert embeds[0].image.url is None
