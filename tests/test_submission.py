from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.core.config import app_settings
from bot.core.enum_classes import BossType
from bot.submission.submission import SheetDetails, StageDetails, Submission

KING_CROAKER = app_settings.bosses["King Croaker"]
SUBMITTER = SimpleNamespace(id=2)
SHEET_DETAILS = SheetDetails(credits="Frosty", damage="37.1B", resonance="225", ascension="M+", notes="Use ult early")


def make_submission(**kwargs) -> Submission:
    return Submission(None, None, SUBMITTER, KING_CROAKER.public, **kwargs)


def test_keeps_only_images_and_videos(make_message, make_attachment):
    message = make_message(
        [
            make_attachment("image/png"),
            make_attachment("text/plain"),
            make_attachment(None),
            make_attachment("video/mp4"),
        ]
    )
    assert len(make_submission(message=message).attachments) == 2


def test_uses_forwarded_snapshot(make_message, make_attachment):
    message = make_message([make_attachment()], content="from the snapshot", forwarded=True)
    submission = make_submission(message=message)
    assert submission.content == "from the snapshot"
    assert len(submission.attachments) == 1


def test_edited_text_replaces_message_text_even_when_empty(make_message):
    message = make_message(content="original")
    assert make_submission(message=message, content="edited").content == "edited"
    assert make_submission(message=message, content="").content == ""


def test_describe_sheet_submission(make_message):
    submission = make_submission(message=make_message(content="Team below"), sheet_details=SHEET_DETAILS)
    submission.author_name = "Author"

    assert submission.describe() == (
        "## Submission\n"
        "**Link:** https://discord.com/channels/1/2/3\n"
        "**From:** Author\n"
        "**Credits:** Frosty\n"
        "**Damage:** 37.1B\n"
        "**Ascension:** M+\n"
        "**Resonance:** 225\n\n"
        "Use ult early\n\n"
        "Team below\n\n"
        "-# Data exported to tracking sheet! ✅"
    )


def test_describe_stage_submission_uses_public_link():
    details = StageDetails(stage="S3", charms_gear="charms", timings="0:30", replays="code", notes="notes")
    submission = Submission(
        None, None, SUBMITTER, app_settings.afk.public, boss_type=BossType.NORMAL, stage_details=details
    )
    submission.author_name = "Me"

    text = submission.describe(public_link="https://public")
    assert text.startswith("## S3\n**Link:** https://public\n**From:** Me\n")
    assert "**Replays:** code" in text
    assert "tracking sheet" not in text


async def test_sheet_export_skipped_without_spreadsheet_id(make_message):
    submission = make_submission(message=make_message(), sheet_details=SHEET_DETAILS)
    with patch("bot.submission.submission.add_row", new=AsyncMock()) as add_row:
        await submission.export_to_sheet()
    add_row.assert_not_awaited()


async def test_sheet_export_uses_message_link(make_message):
    submission = make_submission(message=make_message(), sheet_details=SHEET_DETAILS)
    submission.submission_id = 7
    with (
        patch.object(app_settings, "spreadsheet_id", "sheet"),
        patch("bot.submission.submission.add_row", new=AsyncMock()) as add_row,
    ):
        await submission.export_to_sheet(public_link="https://public")
    args = add_row.await_args.args
    assert args[1:3] == (7, "King Croaker")
    assert args[6] == "https://discord.com/channels/1/2/3"
