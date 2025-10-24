import json
import os


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

setup_json = read_json("setup.json")
aliases_json = read_json("aliases.json")
EMOJIS = read_json("emojis.json")
MAPS = read_json("maps.json")
HEX_CATEGORIES = read_json("hexes.json")

### constants
DR = 'dream_realm'
PL = 'primal_lords'
RR = 'ravaged_realm'

RR_BOSSES = setup_json[RR]

BOT_TOKEN = os.environ['BOT_TOKEN']

### setup_json
SPAM_CHANNEL_ID = setup_json["thread_id"]
SERVER_ID = setup_json["server_id"]
WAITER_ROLE_IDS = setup_json["waiter_role_ids"]
ADMIN_MOD_ROLE_IDS = setup_json["admin_mod_role_ids"]
CHEF_ROLE_ID = setup_json["chef_role_id"]
AMARYLLIS_ID = setup_json["dahlia_id"]

IMAGE_KEYS = ['paragon', 'charms', 'charmspvp', 'charms_reference', 'talents', '!submit prompt']
IMAGE_KEYS.extend(setup_json[DR])
IMAGE_KEYS.extend(setup_json[PL])
IMAGE_KEYS.extend(setup_json[RR])

ROBERTO_ID = 1332595381095366656

PUBLIC_CHANNEL_IDS = setup_json["public_channel_ids"]
PRIVATE_CHANNEL_IDS = setup_json["private_channel_ids"]
STAFF_CHANNEL_IDS = setup_json["staff_channel_ids"]
SPREADSHEET_IDS = setup_json["spreadsheet_ids"]
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