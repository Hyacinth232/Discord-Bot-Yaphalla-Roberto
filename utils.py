import re

from constants import (ALIAS_DICT, EMOJIS, PRIVATE_CHANNEL_IDS,
                       PUBLIC_CHANNEL_IDS, ROBERTO_ID, RR_BOSSES,
                       STAFF_CHANNEL_IDS)
from enum_classes import ChannelType


def sanitize_user_input(value: str) -> str:
    if isinstance(value, str) and value.startswith(("=", "+", "-")):
        return "'" + value
    return value

pub_dict = {id: name for name, id in PUBLIC_CHANNEL_IDS.items()}
priv_dict = {id: name for name, id in PRIVATE_CHANNEL_IDS.items()}
staff_dict = {id: name for name, id in STAFF_CHANNEL_IDS.items()}

def is_pub_channel(id: int) -> bool:
    return id in pub_dict

def is_kitchen_channel(id: int) -> bool:
    return id in pub_dict or id in priv_dict or id in staff_dict

def is_ravaged_realm_channel(id: int) -> bool:
    if id in pub_dict:
        return pub_dict[id] in RR_BOSSES
    if id in priv_dict:
        return priv_dict[id] in RR_BOSSES
    if id in staff_dict:
        return staff_dict[id] in RR_BOSSES
    return False

def to_channel_name(id: int) -> str:
    if id in pub_dict:
        return pub_dict[id]
    if id in priv_dict:
        return priv_dict[id]
    if id in staff_dict:
        return staff_dict[id]
    return ROBERTO_ID

def to_pub_id(id: int) -> int:
    if id in pub_dict:
        return id
    if id in priv_dict:
        return PUBLIC_CHANNEL_IDS[priv_dict[id]]
    if id in staff_dict:
        return PUBLIC_CHANNEL_IDS[staff_dict[id]]
    return None

def to_priv_id(id: int) -> int:
    if id in priv_dict:
        return id
    if id in pub_dict:
        return PRIVATE_CHANNEL_IDS[pub_dict[id]]
    if id in staff_dict:
        return PRIVATE_CHANNEL_IDS[staff_dict[id]]
    return None
    
def to_staff_id(id: int) -> int:
    if id in staff_dict:
        return id
    if id in pub_dict:
        return STAFF_CHANNEL_IDS[pub_dict[id]]
    if id in priv_dict:
        return STAFF_CHANNEL_IDS[priv_dict[id]]
    return None

def to_channel_type_id(channel_type: ChannelType, channel_id: int):
    if channel_type == ChannelType.PUBLIC:
        return to_pub_id(channel_id)
    
    if channel_type == ChannelType.PRIVATE:
        return to_priv_id(channel_id)
    
    if channel_type == ChannelType.STAFF:
        return to_staff_id(channel_id)
    
    return None

def get_emoji(name: str):
    emoji_name = name.replace('-', '').replace('&', '')
    return '<:{}:{}>'.format(emoji_name, str(EMOJIS.get(emoji_name, name)))

def replace_emojis(text):
    pattern = r':([a-zA-Z0-9_]+):'

    def replacer(match):
        yap_name = match.group(1)
        emoji_name = yap_name.removeprefix('yap')
        return get_emoji(emoji_name)

    return re.sub(pattern, replacer, text)

def split_input(input: str) -> list[str]:
    return [text for text in re.split(r'[，,、\s]+', input) if text]

def translate_name(name: str, alias_dict: dict=ALIAS_DICT):
    name = name.title()
    if name in alias_dict:
        name = alias_dict[name]
    return name

def clean_input_str(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9 ?!\'\-\(\):,]', '', text)
    #text = text.title()
    return text