"""Application configuration using Pydantic Settings."""

import json
import logging
import os
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _get_base_path() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def _load_json_file(json_path: Path) -> dict:
    """Load and return JSON data from a file."""
    if not json_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {json_path}")

    logger.info("Reading config file: %s", json_path)
    with json_path.open() as f:
        return json.load(f)


CONFIG_DIR = _get_base_path() / "config"


def _environment() -> str:
    """Name of the environment config to load: config/<name>.json.

    ENVIRONMENT wins when set; otherwise Heroku (which sets DYNO) is production and anything else is test.
    """
    if environment := os.environ.get("ENVIRONMENT"):
        return environment.lower()
    return "production" if "DYNO" in os.environ else "test"


class _ConfigModel(BaseModel):
    """Base for config sections: unknown keys are rejected so typos fail at startup."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Roles(_ConfigModel):
    """Server role IDs."""

    waiter: list[int] = Field(..., description="Roles allowed to use staff commands")
    stage: list[int] = Field(..., description="Roles allowed to submit AFK stages")
    benchmark: int = Field(..., description="Role pinged by /benchmark")
    souschef: int = Field(..., description="Role pinged by /souschef")


class BossChannels(_ConfigModel):
    """A boss's public kitchen channel and the private channel its submissions are forwarded to."""

    public: int
    private: int


class AfkChannels(_ConfigModel):
    """The AFK kitchen channel and the private channels for each stage type."""

    public: int
    normal: int
    phantimal: int


class GameModes(_ConfigModel):
    """Boss names for each game mode; each must have an entry in the environment's bosses."""

    dream_realm: list[str] = Field(..., description="Rotated daily, in order, from start_date")
    primal_lords: list[str]
    ravaged_realm: list[str]
    titan_reaver: list[str]


class AppSettings(BaseSettings):
    """Discord bot settings.

    Merged from config/shared.json (game data, the same for every server), the environment's
    file (config/<ENVIRONMENT>.json, holding that server's IDs) and .env (secrets).
    """

    bot_token: str = Field(..., description="Discord bot token")

    # shared.json
    amaryllis_id: int = Field(..., description="Amaryllis user ID")
    season: int = Field(..., description="Current season number, shown in boss guide titles")
    start_date: datetime = Field(..., description="Season start (UTC); day 0 of the boss channel rotation")
    game_modes: GameModes

    # production.json / test.json
    server_id: int = Field(..., description="Discord server ID")
    spreadsheet_id: str | None = Field(
        default=None, description="Tracking sheet ID; sheet export is skipped when unset"
    )
    souschef_extra_channel_ids: list[int] = Field(
        default_factory=list, description="Non-kitchen channels where /souschef is also allowed"
    )
    roles: Roles
    afk: AfkChannels
    bosses: dict[str, BossChannels] = Field(..., description="Kitchen channels by boss name")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def load(cls, config_dir: Path = CONFIG_DIR, environment: str | None = None) -> Self:
        """Load settings from the shared and environment JSON files plus environment variables."""
        shared_data = _load_json_file(config_dir / "shared.json")
        env_data = _load_json_file(config_dir / f"{environment or _environment()}.json")

        overlap = shared_data.keys() & env_data.keys()
        if overlap:
            raise ValueError(f"Keys set in both shared and environment config: {', '.join(sorted(overlap))}")

        merged_data = {**shared_data, **env_data}
        unknown = merged_data.keys() - cls.model_fields.keys()
        if unknown:
            raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown))}")

        return cls(**merged_data)

    @cached_property
    def image_keys(self) -> list[str]:
        """List of all image keys including bosses."""
        keys = ["paragon", "charms", "charmspvp", "charms_reference", "talents"]
        keys.extend(self.game_modes.dream_realm)
        keys.extend(self.game_modes.primal_lords)
        keys.extend(self.game_modes.ravaged_realm)
        return keys

    @model_validator(mode="after")
    def validate_rotation_channels(self) -> Self:
        """The daily rotation needs channels for every Dream Realm boss."""
        missing = [name for name in self.game_modes.dream_realm if name not in self.bosses]
        if missing:
            raise ValueError(f"Missing channels in bosses for Dream Realm: {', '.join(missing)}")
        return self


class DatabaseSettings(BaseSettings):
    """Database and external service settings."""

    mongo_uri: str = Field(..., description="MongoDB connection URI")
    google_sa_json: str = Field(..., description="Google Service Account JSON as string")

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


class DataSettings(BaseSettings):
    """Game data loaded from JSON files."""

    base_dir: Path = Field(default_factory=_get_base_path, description="Project root directory")

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    @cached_property
    def emojis(self) -> dict:
        """Emojis JSON data."""
        return _load_json_file(self.base_dir / "data" / "emojis.json")


app_settings = AppSettings.load()
db_settings = DatabaseSettings()
data_settings = DataSettings()
