import json
import os

import gspread.exceptions
from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager

from bot.core.config import db_settings
from bot.core.utils import sanitize_user_input

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
        worksheet = await spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=11
        )
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
            "Image"
        ]
        await worksheet.append_row(headers, value_input_option="USER_ENTERED")
        return worksheet

async def add_row(
    num_id: int,
    boss_name: str,
    author_name: str,
    resonance: str,
    ascension: str,
    url: str,
    credit_name: str,
    damage: str,
    notes: str,
    units: dict=None,
    image_url: str=None
    ):
    """Add a new row to the Google Sheet for the specified boss."""
    # print(f"Adding row for num_id {num_id} in {boss_name}")
    try:
        sheet_id = db_settings.spreadsheet_ids["Dream Realm"]
        gc = await agcm.authorize()
        sh = await gc.open_by_key(sheet_id)
        ws = await get_or_create_worksheet(sh, boss_name)
        
        units_str = ""
        image_str = ""
        if units:
            units_list = [dictionary['name'] for dictionary in units]
            
            if "Elijah" in units_list and "Lailah" in units_list:
                units_list.remove("Elijah")
                units_list.remove("Lailah")
                units_list.append("Twins")
                
            if "Real" in units_list and "Fake" in units_list:
                units_list.remove("Real")
                units_list.remove("Fake")
                units_list.append("Phraesto")
                
            units_list = [unit for unit in units_list if unit != "Turret"]
            units_list.sort()
            
            units_str = ", ".join(units_list)
            
        if image_url:
            image_str = '=IMAGE("{}")'.format(image_url)
        
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
            units_str,
            image_str]
        
        await ws.append_row(
            row,
            value_input_option="USER_ENTERED",
            table_range="A2",
            insert_data_option="INSERT_ROWS"
        )

    except Exception as e:
        print(e)


async def clear_image_str(num_id: int, boss_name: str):
    """Clear the image_str and units_str columns for rows matching the given num_id."""
    # print(f"Clearing image_str and units_str for num_id {num_id} in {boss_name}")
    try:
        sheet_id = db_settings.spreadsheet_ids[boss_name]
        gc = await agcm.authorize()
        sh = await gc.open_by_key(sheet_id)
        ws = await get_or_create_worksheet(sh, "Roberto")
        
        all_values = await ws.get_all_values()
        
        num_id_col = 0
        units_str_col = 9  # Column J
        image_str_col = 10  # Column K
        
        rows_to_update = []
        for idx, row in enumerate(all_values, start=1):
            if idx == 1:
                continue
            if len(row) > num_id_col and str(row[num_id_col]) == str(num_id):
                rows_to_update.append(idx)
        
        for row_num in rows_to_update:
            await ws.update_cell(row_num, units_str_col + 1, "")
            await ws.update_cell(row_num, image_str_col + 1, "")
        
    except Exception as e:
        print(f"Error clearing image_str and units_str for num_id {num_id} in {boss_name}: {e}")


