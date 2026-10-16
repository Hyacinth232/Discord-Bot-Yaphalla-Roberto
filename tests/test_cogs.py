"""Command handlers called directly with mocked interactions; nothing talks to Discord."""

import io
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from PIL import Image

from bot.cogs.rotation import visible_bosses
from bot.cogs.utilities import Utilities
from bot.services.infographic_service import InfographicService

BOSSES = ["A", "B", "C"]
START = datetime(2026, 9, 23, tzinfo=UTC)


@pytest.mark.parametrize(
    ("days", "expected"),
    [(0, {"A", "B"}), (1, {"B", "C"}), (2, {"C", "A"}), (3, {"A", "B"})],
)
def test_rotation_shows_today_and_tomorrow(days: int, expected: set[str]):
    assert visible_bosses(BOSSES, START, START + timedelta(days=days, hours=23)) == expected


@pytest.fixture
def utilities() -> Utilities:
    return Utilities(MagicMock())


async def test_webp_rejects_non_images(utilities, interaction, make_attachment):
    await utilities.webp.callback(utilities, interaction, make_attachment("text/plain"), 80, False)
    interaction.response.send_message.assert_awaited_once_with("Please choose an image.", ephemeral=True)


async def test_webp_posts_converted_image_and_link(utilities, interaction, make_attachment):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buffer, "PNG")
    sent = MagicMock(attachments=[MagicMock(url="https://cdn/team.webp")], edit=AsyncMock())
    interaction.followup.send.return_value = sent

    await utilities.webp.callback(
        utilities, interaction, make_attachment(data=buffer.getvalue(), filename="team.png"), 80, False
    )

    interaction.response.defer.assert_awaited_once()
    assert interaction.followup.send.await_args.kwargs["file"].filename == "team.webp"
    assert "https://cdn/team.webp" in sent.edit.await_args.kwargs["content"]


async def test_webp_reports_unreadable_images(utilities, interaction, make_attachment):
    await utilities.webp.callback(utilities, interaction, make_attachment(data=b"garbage"), 80, False)
    assert "Couldn't read" in interaction.followup.send.await_args.args[0]


async def test_context_menu_uses_first_image_in_message(utilities, interaction, make_message, make_attachment):
    message = make_message([make_attachment("video/mp4"), make_attachment(data=b"garbage", filename="second.png")])
    await utilities.convert_message_to_webp(interaction, message)
    assert "second.png" in interaction.followup.send.await_args.args[0]


async def test_infographic_formatting():
    db = MagicMock()
    db.get_image_link = AsyncMock(return_value={"text": "https://img", "timestamp": 123})
    db.set_image_link = AsyncMock()
    service = InfographicService(db)

    assert await service.get("paragon") == "https://img\n<t:123>"

    db.get_image_link.return_value = None
    assert await service.get("missing") is None
