import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.core.config import CONFIG_DIR, AppSettings


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """A copy of the real shared config and the example environment config."""
    shutil.copy(CONFIG_DIR / "shared.json", tmp_path / "shared.json")
    shutil.copy(CONFIG_DIR / "example.json", tmp_path / "example.json")
    return tmp_path


def edit_example(config_dir: Path, change):
    path = config_dir / "example.json"
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def test_example_config_loads(config_dir: Path):
    settings = AppSettings.load(config_dir, "example")
    assert settings.roles.benchmark == 100000000000000003
    assert settings.bosses["King Croaker"].private == 100000000000000021
    assert settings.spreadsheet_id is None


@pytest.mark.parametrize("environment", ["production"])
def test_committed_environment_configs_load(environment: str):
    AppSettings.load(CONFIG_DIR, environment)


def test_rejects_unknown_top_level_key(config_dir: Path):
    edit_example(config_dir, lambda data: data.update(sever_id=1))
    with pytest.raises(ValueError, match="Unknown config keys: sever_id"):
        AppSettings.load(config_dir, "example")


def test_rejects_unknown_nested_key(config_dir: Path):
    edit_example(config_dir, lambda data: data["roles"].update(waiters=[]))
    with pytest.raises(ValidationError, match="waiters"):
        AppSettings.load(config_dir, "example")


def test_rejects_key_set_in_both_files(config_dir: Path):
    edit_example(config_dir, lambda data: data.update(season=9))
    with pytest.raises(ValueError, match="both shared and environment config: season"):
        AppSettings.load(config_dir, "example")


def test_requires_channels_for_every_dream_realm_boss(config_dir: Path):
    edit_example(config_dir, lambda data: data["bosses"].pop("Novik"))
    with pytest.raises(ValidationError, match="Missing channels in bosses for Dream Realm: Novik"):
        AppSettings.load(config_dir, "example")


def test_missing_environment_file(config_dir: Path):
    with pytest.raises(FileNotFoundError):
        AppSettings.load(config_dir, "staging")
