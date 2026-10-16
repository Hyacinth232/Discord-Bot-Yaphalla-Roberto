import logging
from datetime import datetime

import discord
import gspread.exceptions
from google.oauth2.service_account import Credentials
from gspread.utils import ValueInputOption
from gspread_asyncio import AsyncioGspreadClientManager

from bot.core.config import app_settings, db_settings
from bot.core.utils import sanitize_user_input

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_creds_from_env():
    """Get Google Sheets credentials from environment."""
    return Credentials.from_service_account_info(db_settings.google_sheets_info, scopes=SCOPES)


agcm = AsyncioGspreadClientManager(_get_creds_from_env)


async def get_or_create_worksheet(spreadsheet: gspread.Spreadsheet, worksheet_name: str = "Roberto"):
    """Get worksheet by name, or create it if it doesn't exist."""
    try:
        worksheet = await spreadsheet.worksheet(worksheet_name)
        return worksheet
    except gspread.exceptions.WorksheetNotFound:
        worksheet = await spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=13)
        headers = [
            "Boss Name",
            "ID",
            "Author Name",
            "Ascension",
            "Resonance",
            "URL",
            "Credit Name",
            "",
            "Damage",
            "Notes",
            "Units",
            "Image",
            "Date",
        ]
        await worksheet.append_row(headers, value_input_option=ValueInputOption.user_entered)
        return worksheet


async def add_row(
    bot: discord.Client,
    num_id: int,
    boss_name: str,
    author_name: str,
    resonance: str,
    ascension: str,
    url: str,
    credit_name: str,
    damage: str,
    notes: str,
):
    """Add a new row to the boss's sheet and to the combined Roberto sheet."""
    try:
        gc = await agcm.authorize()
        sh = await gc.open_by_key(app_settings.spreadsheet_id)

        # Units and Image columns were filled by the retired image recognition; they are left blank
        row = [
            boss_name,
            str(num_id),
            sanitize_user_input(author_name),
            sanitize_user_input(ascension),
            sanitize_user_input(resonance),
            url,
            sanitize_user_input(credit_name),
            "",
            sanitize_user_input(damage),
            sanitize_user_input(notes),
            "",
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]

        for sheet_name in [boss_name, "Roberto"]:
            ws = await get_or_create_worksheet(sh, sheet_name)

            await ws.append_row(
                row,
                value_input_option=ValueInputOption.user_entered,
                table_range="A2",
                insert_data_option="INSERT_ROWS",
            )

    except Exception as e:
        logger.exception("Failed to add row to spreadsheet")
        amaryllis = await bot.fetch_user(app_settings.amaryllis_id)
        await amaryllis.send(f"Error adding row to spreadsheet: {e}")
