import json
import os

from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager

from constants import GSHEETS_INFO, SPREADSHEET_IDS
from utils import sanitize_user_input

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

agcm = AsyncioGspreadClientManager(
    Credentials.from_service_account_info(GSHEETS_INFO, scopes=SCOPES)
    )

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
    try:
        sheet_id = SPREADSHEET_IDS[boss_name]
        gc = await agcm.authorize()
        sh = await gc.open_by_key(sheet_id)
        ws = await sh.worksheet("Roberto")
        
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
    


