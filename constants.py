import json
import os

from dotenv import load_dotenv

load_dotenv()

MODE = True


### Housekeeping
def read_json(file_name) -> dict:
    print("Reading config file: {}".format(file_name))
    with open(file_name, "r") as f:
        data = json.load(f)
    return data

with open( "usage.txt", "r") as f:
    USAGE = f.read()
    
with open("roberto.txt", "r") as f:
    ROBERTO_TEXT = f.read()

# Load configuration files
shared_config = read_json("setup_shared.json")
setup_production = read_json("setup_production.json")
setup_test = read_json("setup_test.json")

aliases_json = read_json("aliases.json")
EMOJIS = read_json("emojis.json")
MAPS = read_json("maps.json")
HEX_CATEGORIES = read_json("hexes.json")

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
# Determine if we're in production mode
# Check for explicit ENVIRONMENT variable, or if running on Heroku (DYNO is set)
IS_PRODUCTION = os.environ.get('ENVIRONMENT', '').lower() == 'production' or os.environ.get('DYNO') is not None

# Select server and channel IDs based on environment
env_config = setup_production if IS_PRODUCTION else setup_test
SERVER_ID = env_config["server_id"]
SPAM_CHANNEL_ID = env_config["thread_id"]
PUBLIC_CHANNEL_IDS = env_config["public_channel_ids"]
PRIVATE_CHANNEL_IDS = env_config["private_channel_ids"]
STAFF_CHANNEL_IDS = env_config["staff_channel_ids"]

# Shared configuration (same for both environments)
WAITER_ROLE_IDS = shared_config["waiter_role_ids"]
ADMIN_MOD_ROLE_IDS = shared_config["admin_mod_role_ids"]
CHEF_ROLE_ID = shared_config["chef_role_id"]
AMARYLLIS_ID = shared_config["dahlia_id"]

IMAGE_KEYS = ['paragon', 'charms', 'charmspvp', 'charms_reference', 'talents', '!submit prompt']
IMAGE_KEYS.extend(shared_config[DR])
IMAGE_KEYS.extend(shared_config[PL])
IMAGE_KEYS.extend(shared_config[RR])

ROBERTO_ID = 1332595381095366656
SPREADSHEET_IDS = shared_config["spreadsheet_ids"]
CHANNEL_IDS_DICT = {pub_id : PRIVATE_CHANNEL_IDS[name] for name, pub_id in PUBLIC_CHANNEL_IDS.items()}
STAFF_CHANNEL_IDS_DICT = {pub_id : STAFF_CHANNEL_IDS[name] for name, pub_id in PUBLIC_CHANNEL_IDS.items()}

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