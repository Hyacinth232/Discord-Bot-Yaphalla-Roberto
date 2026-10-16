"""Test setup: load config/example.json with dummy secrets instead of a developer's real config and .env."""

import os

# Must run before any bot module is imported, since config loads at import time
os.environ["ENVIRONMENT"] = "example"
os.environ["BOT_TOKEN"] = "test-token"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["GOOGLE_SA_JSON"] = "{}"

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest


@pytest.fixture
def make_attachment():
    """Build a stand-in for discord.Attachment."""

    def make(content_type: str | None = "image/png", filename: str = "image.png", data: bytes = b""):
        attachment = MagicMock(spec=discord.Attachment)
        attachment.content_type = content_type
        attachment.filename = filename
        attachment.read = AsyncMock(return_value=data)
        return attachment

    return make


@pytest.fixture
def make_message():
    """Build a stand-in for discord.Message, optionally forwarded."""

    def make(attachments=(), content: str = "", forwarded: bool = False, author_id: int = 1):
        source = SimpleNamespace(attachments=list(attachments), content=content)
        message = MagicMock(spec=discord.Message)
        message.flags = SimpleNamespace(forwarded=forwarded)
        message.message_snapshots = [source] if forwarded else []
        message.attachments = [] if forwarded else source.attachments
        message.content = "" if forwarded else content
        message.jump_url = "https://discord.com/channels/1/2/3"
        message.author = SimpleNamespace(id=author_id)
        return message

    return make


@pytest.fixture
def interaction():
    """A stand-in for discord.Interaction with async response and followup methods."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction
