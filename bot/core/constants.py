import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODE = True


### Housekeeping
# Project root is 3 levels up
_BASE_DIR = Path(__file__).resolve().parent.parent.parent

def read_json(file_path: Path | str) -> dict:
    """Read JSON file from Path object or string path."""
    print("Reading config file: {}".format(file_path))
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

# Read text files using Path objects directly
USAGE = (_BASE_DIR / "usage.txt").read_text()
ROBERTO_TEXT = (_BASE_DIR / "roberto.txt").read_text()

# Load configuration files - Path objects work directly with open()
shared_config = read_json(_BASE_DIR / "config" / "setup_shared.json")
setup_production = read_json(_BASE_DIR / "config" / "setup_production.json")
setup_test = read_json(_BASE_DIR / "config" / "setup_test.json")

aliases_json = read_json(_BASE_DIR / "data" / "aliases.json")
EMOJIS = read_json(_BASE_DIR / "data" / "emojis.json")
MAPS = read_json(_BASE_DIR / "data" / "maps.json")
HEX_CATEGORIES = read_json(_BASE_DIR / "data" / "hexes.json")

### Asset Paths
# All asset paths centralized here for easy maintenance
HEXES_FOLDER = _BASE_DIR / "assets" / "images" / "hexes"
ICON_PATH = _BASE_DIR / "assets" / "images" / "icon.png"
YAP_PATH = _BASE_DIR / "assets" / "images" / "Yap.png"
FONT_PATH = _BASE_DIR / "assets" / "fonts" / "Lato-Regular.ttf"
CIRC_FOLDER = _BASE_DIR / "assets" / "images" / "templates"

### constants
DR = 'dream_realm'
PL = 'primal_lords'
RR = 'ravaged_realm'

RR_BOSSES = shared_config[RR]

if os.environ.get("GOOGLE_SA_JSON"):
    GSHEETS_INFO = json.loads(os.environ["GOOGLE_SA_JSON"])
else:
    raise FileNotFoundError("GOOGLE_SA_JSON environment variable is required")

MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

### setup_json
IS_PRODUCTION = os.environ.get('ENVIRONMENT', '').lower() == 'production' or os.environ.get('DYNO') is not None

# Select server and channel IDs based on environment
env_config = setup_production if IS_PRODUCTION else setup_test
SERVER_ID = env_config["server_id"]
SPAM_CHANNEL_ID = env_config["thread_id"]
PUBLIC_CHANNEL_IDS = env_config["public_channel_ids"]
PRIVATE_CHANNEL_IDS = env_config["private_channel_ids"]

# Shared configuration (same for both environments)
WAITER_ROLE_IDS = shared_config["waiter_role_ids"]
STAGE_ROLE_IDS = shared_config["stage_role_ids"]
ADMIN_MOD_ROLE_IDS = shared_config["admin_mod_role_ids"]
CHEF_ROLE_ID = shared_config["chef_role_id"]
AMARYLLIS_ID = shared_config["dahlia_id"]

IMAGE_KEYS = ['paragon', 'charms', 'charmspvp', 'charms_reference', 'talents', '!submit prompt']
IMAGE_KEYS.extend(shared_config[DR])
IMAGE_KEYS.extend(shared_config[PL])
IMAGE_KEYS.extend(shared_config[RR])

ROBERTO_ID = 1332595381095366656
SPREADSHEET_IDS = shared_config["spreadsheet_ids"]

### HEX_CATEGORIES
UNITS = [hex_name for lst in HEX_CATEGORIES['Units'].values() for hex_name in lst]
ARTIFACTS = [hex_name for lst in HEX_CATEGORIES['Artifacts'].values() for hex_name in lst]
FILLS = [hex_name for hex_name in HEX_CATEGORIES['Base']['Fill']]
LINES = [hex_name for hex_name in HEX_CATEGORIES['Base']['Line']]
ALL_HEX_NAMES  = [hex_name for factions in HEX_CATEGORIES.values() for lst in factions.values() for hex_name in lst]

### aliases_json
ARENA_DICT = aliases_json["arena_names"]
ALIAS_DICT = aliases_json["units"]

### ALIAS_DICT =aliases_json["cn_nicknames"] | aliases_json["simplified_cn"] | aliases_json["cn_artifacts"] | 

# sorted constants
ALL_VALID_NAMES = sorted(list(ALIAS_DICT.keys()) + ALL_HEX_NAMES)
ARENA_NAMES = sorted(aliases_json["arena_names"])