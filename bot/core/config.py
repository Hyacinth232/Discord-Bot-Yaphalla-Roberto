"""Application configuration using Pydantic Settings"""
import json
import logging
import os
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger()


def _get_base_path() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def _load_json_file(json_path: Path) -> dict:
    """Load and return JSON data from a file."""
    if not json_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {json_path}")
    
    logger.info("Reading config file: %s", json_path)
    with open(json_path, "r") as f:
        return json.load(f)


def _get_environment_config_path() -> Path:
    """Determine which environment config file to use."""
    base_path = _get_base_path()
    config_dir = base_path / "config"
    
    is_production = (
        os.environ.get('ENVIRONMENT', '').lower() == 'production' 
        or os.environ.get('DYNO') is not None
    )
    
    if is_production:
        return config_dir / "setup_production.json"
    else:
        return config_dir / "setup_test.json"


class AppSettings(BaseSettings):
    """Discord bot application settings."""
    
    bot_token: str = Field(..., description="Discord bot token")
    server_id: int = Field(..., description="Discord server ID")
    thread_id: int = Field(..., description="Thread ID for spam channel")
    
    public_channel_names_to_ids: dict[str, int] = Field(
        ...,
        description="Mapping of public channel names to IDs"
    )
    private_channel_names_to_ids: dict[str, int] = Field(
        ...,
        description="Mapping of private channel names to IDs"
    )
    
    admin_mod_role_ids: list[int] = Field(..., description="Admin/mod role IDs")
    waiter_role_ids: list[int] = Field(..., description="Waiter role IDs")
    chef_role_id: int = Field(..., description="Chef role ID")
    stage_role_ids: list[int] = Field(..., description="Stage role IDs")
    
    amaryllis_id: int = Field(..., description="Amaryllis user ID")
    burger_king_id: int = Field(..., description="Burger King channel ID")
    
    dream_realm_bosses: list[str] = Field(
        ..., 
        description="List of Dream Realm boss names to rotate through"
    )
    ravaged_realm: list[str] = Field(..., description="Ravaged Realm boss names")
    primal_lords: list[str] = Field(..., description="Primal Lords boss names")
    titan_reaver: list[str] = Field(..., description="Titan Reaver boss names")
    misc: list[str] = Field(..., description="Miscellaneous categories")
    
    start_date: datetime = Field(
        default_factory=lambda: datetime(2026, 1, 30, tzinfo=timezone.utc),
        description="Start date for rotation calculation"
    )
    
    roberto_id: int = Field(
        default=1332595381095366656,
        description="Roberto bot user ID"
    )
    
    spreadsheet_id: str | None = Field(
        default=None,
        description="Default Google Sheets spreadsheet ID"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    @classmethod
    def load(cls) -> Self:
        """Load settings from multiple JSON files and environment variables."""
        base_path = _get_base_path()
        config_dir = base_path / "config"
        
        shared_path = config_dir / "setup_shared.json"
        shared_data = _load_json_file(shared_path)
        
        env_config_path = _get_environment_config_path()
        env_data = _load_json_file(env_config_path)
        
        merged_data = {**shared_data, **env_data}
        merged_data_lower = {k.lower(): v for k, v in merged_data.items()}
        
        return cls(**merged_data_lower)
    
    @cached_property
    def image_keys(self) -> list[str]:
        """List of all image keys including bosses."""
        keys = ['paragon', 'charms', 'charmspvp', 'charms_reference', 'talents', '!submit prompt']
        keys.extend(self.dream_realm_bosses)
        keys.extend(self.primal_lords)
        keys.extend(self.ravaged_realm)
        return keys
    
    @cached_property
    def shared_config(self) -> dict[str, list[str]]:
        """Helper dict for accessing boss lists by game mode."""
        return {
            'dream_realm_bosses': self.dream_realm_bosses,
            'dream_realm': self.dream_realm_bosses,  # Alias for compatibility
            'primal_lords': self.primal_lords,
            'ravaged_realm': self.ravaged_realm,
            'titan_reaver': self.titan_reaver,
            'misc': self.misc,
        }
    
    @model_validator(mode="after")
    def validate_dream_realm_channels(self) -> Self:
        """Ensure all dream_realm_bosses have corresponding channel IDs."""
        missing_public = []
        missing_private = []
        
        for boss_name in self.dream_realm_bosses:
            if boss_name not in self.public_channel_names_to_ids:
                missing_public.append(boss_name)
            if boss_name not in self.private_channel_names_to_ids:
                missing_private.append(boss_name)
        
        if missing_public:
            raise ValueError(
                f"Missing public channel IDs for: {', '.join(sorted(missing_public))}"
            )
        if missing_private:
            raise ValueError(
                f"Missing private channel IDs for: {', '.join(sorted(missing_private))}"
            )
        
        return self


class DatabaseSettings(BaseSettings):
    """Database and external service settings."""
    
    mongo_uri: str = Field(..., description="MongoDB connection URI")
    google_sa_json: str = Field(..., description="Google Service Account JSON as string")
    spreadsheet_ids: dict[str, str] | None = Field(
        default=None,
        description="Mapping of sheet names to Google Sheets IDs"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    @cached_property
    def google_sheets_info(self) -> dict:
        """Parse Google Service Account JSON."""
        return json.loads(self.google_sa_json)


class PathSettings(BaseSettings):
    """File paths and asset directory settings."""
    
    base_dir: Path = Field(
        default_factory=_get_base_path,
        description="Project root directory"
    )
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )
    
    @property
    def hexes_folder(self) -> Path:
        """Path to hexes images folder."""
        return self.base_dir / "assets" / "images" / "hexes"
    
    @property
    def icon_path(self) -> Path:
        """Path to icon.png file."""
        return self.base_dir / "assets" / "images" / "icon.png"
    
    @property
    def yap_path(self) -> Path:
        """Path to Yap.png file."""
        return self.base_dir / "assets" / "images" / "Yap.png"
    
    @property
    def font_path(self) -> Path:
        """Path to Lato-Regular.ttf font file."""
        return self.base_dir / "assets" / "fonts" / "Lato-Regular.ttf"
    
    @property
    def templates_folder(self) -> Path:
        """Path to templates folder."""
        return self.base_dir / "assets" / "images" / "templates"


class DataSettings(BaseSettings):
    """Game data loaded from JSON files."""
    
    base_dir: Path = Field(
        default_factory=_get_base_path,
        description="Project root directory"
    )
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )
    
    @cached_property
    def aliases_json(self) -> dict:
        """Aliases JSON data."""
        return _load_json_file(self.base_dir / "data" / "aliases.json")
    
    @cached_property
    def emojis(self) -> dict:
        """Emojis JSON data."""
        return _load_json_file(self.base_dir / "data" / "emojis.json")
    
    @cached_property
    def maps(self) -> dict:
        """Maps JSON data."""
        return _load_json_file(self.base_dir / "data" / "maps.json")
    
    @cached_property
    def hex_categories(self) -> dict:
        """Hex categories JSON data."""
        return _load_json_file(self.base_dir / "data" / "hexes.json")
    
    @cached_property
    def arena_dict(self) -> dict:
        """Arena names dictionary."""
        return self.aliases_json["arena_names"]
    
    @cached_property
    def alias_dict(self) -> dict:
        """Unit aliases dictionary."""
        return self.aliases_json["units"]
    
    @cached_property
    def units(self) -> list[str]:
        """List of all unit hex names."""
        return [
            hex_name 
            for lst in self.hex_categories['Units'].values() 
            for hex_name in lst
        ]
    
    @cached_property
    def artifacts(self) -> list[str]:
        """List of all artifact hex names."""
        return [
            hex_name 
            for lst in self.hex_categories['Artifacts'].values() 
            for hex_name in lst
        ]
    
    @cached_property
    def fills(self) -> list[str]:
        """List of fill hex names."""
        return [hex_name for hex_name in self.hex_categories['Base']['Fill']]
    
    @cached_property
    def lines(self) -> list[str]:
        """List of line hex names."""
        return [hex_name for hex_name in self.hex_categories['Base']['Line']]
    
    @cached_property
    def all_hex_names(self) -> list[str]:
        """List of all hex names from all categories."""
        return [
            hex_name 
            for factions in self.hex_categories.values() 
            for lst in factions.values() 
            for hex_name in lst
        ]
    
    @cached_property
    def all_valid_names(self) -> list[str]:
        """Sorted list of all valid unit/hex names."""
        return sorted(list(self.alias_dict.keys()) + self.all_hex_names)
    
    @cached_property
    def arena_names(self) -> list[str]:
        """Sorted list of arena names."""
        return sorted(self.aliases_json["arena_names"])


app_settings = AppSettings.load()
db_settings = DatabaseSettings()
path_settings = PathSettings()
data_settings = DataSettings()
