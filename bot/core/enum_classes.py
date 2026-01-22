from enum import Enum

from bot.core.constants import ARTIFACTS, UNITS


class Exit_Status(Enum):
    OKAY = 0
    DATABASE = -1
    NAME_EXISTS = -2
    OTHER = -3
    
    def __bool__(self) -> bool:
        return self == Exit_Status.OKAY

class Tile(Enum):
    ARTIFACT = 0
    UNIT = 1
    OTHER = 2
    
    @classmethod
    def get_idx_type(cls, idx: int):
        return cls.ARTIFACT if idx < 0 else cls.UNIT if idx > 0 else cls.OTHER
    
    @classmethod
    def get_name_type(cls, name: str):
        if name in ARTIFACTS: return cls.ARTIFACT
        if name in UNITS: return cls.UNIT
        return cls.OTHER
    
    def convert_idx(self, idx: int) -> int:
        return idx if self == Tile.UNIT else -idx if self == Tile.ARTIFACT else 0
    
    def __str__(self) -> str:
        return "units" if self == Tile.UNIT else "artifacts" if self == Tile.ARTIFACT else None

class ChannelType(Enum):
    PUBLIC = 0
    PRIVATE = 1
    STAFF = 2
    
class BossType(Enum):
    NORMAL = 0
    PHANTIMAL = 1
    DREAM_REALM = 2
    RAVAGED_REALM = 3
    PRIMAL_LORD = 4
    MISC = 5

class Language(Enum):
    EN = 0
    CN = 1
    
TRANSLATE = {
    'Added': {
        Language.EN: 'Added ',
        Language.CN: '添加'
        },
    'Removed': {
        Language.EN: 'Removed ',
        Language.CN: '移除'
    },
    'Swapped': {
        Language.EN: 'Swapped ',
        Language.CN: '交换'
    },
    'Error': {
        Language.EN: 'Something went wrong.',
        Language.CN: '出错了'
    },
    'Clear': {
        Language.EN: 'Your current formation has been cleared.',
        Language.CN: '清空了'
    }
    }